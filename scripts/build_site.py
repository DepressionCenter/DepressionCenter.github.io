#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# build_site.py - Generate the static Open Source Hub site from the GitHub API.
# Author(s): Gabriel Mongefranco.
# Created: 2026-09-01
# Last Modified: 2026-09-01
# Summary: Read the organization's public repositories, their READMEs, and their preview images,
#          then write finished HTML pages so the site needs no JavaScript to show its content
#          and search engines can read every repository description and README.
# Notes: See README file for documentation and full license information.
# Website: https://code.depressioncenter.org/
#
# Copyright (c) 2026 The Regents of the University of Michigan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
"""Build the Open Source Hub as static files.

Run nightly by .github/workflows/build-site.yml, and by hand during development. Everything
this script reads comes from the public GitHub API, so it needs no credentials; inside a
workflow it uses the automatically provided GITHUB_TOKEN purely for the higher rate limit.

All content fetched from GitHub is treated as untrusted input: text is HTML-escaped, README
markup is passed through an allowlist sanitizer, and link targets are restricted to http,
https, and mailto.
"""

import argparse
import concurrent.futures
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import nh3
from PIL import Image

from imagelib import (
    FULL_MAX_WIDTH,
    THUMB_MAX_WIDTH,
    flatten_for_png,
    normalize_preview,
    save_png,
)

### Load Configuration ###

ROOT = Path(__file__).resolve().parent.parent

# The GitHub organization whose public repositories are published on this site.
ORG = "DepressionCenter"

# Where the finished site is served. Used for canonical URLs, Open Graph tags, and the sitemap.
SITE_BASE_URL = "https://code.depressioncenter.org"
SITE_TITLE = "Open Source Hub | Eisenberg Family Depression Center"
SITE_DESCRIPTION = (
    "Eisenberg Family Depression Center open source hub — accelerating mental health "
    "discoveries through code."
)

# First path segment for the generated repository pages. This must never match the name of a
# repository in the organization: GitHub Pages resolves a project site by that first segment,
# so a repository called "repos" would shadow every page written here. Checked at build time.
DETAIL_PATH_PREFIX = "repos"

# Repositories that exist for infrastructure reasons and are not products of their own.
IGNORED_REPOS = {".github", ".github-private", "DepressionCenter.github.io"}

# Topics that describe the organization rather than the project, so they add nothing as tags.
IGNORE_TOPICS = {"umich", "#umich", "u-m", "um", "efdc", "depressioncenter"}
MAX_TAGS = 7

# Repository holding the canonical preview-image placeholders. A repository created from the
# template but never customized carries byte-identical copies; those are ignored so the
# hand-made thumbnail in images/repo-previews/ is used instead.
TEMPLATE_REPO = "EFDC-Repo-Template"
TEMPLATE_PLACEHOLDER_PATHS = ("images/repo-preview.png", "images/repo-preview-thumb.png")

# Preview images larger than this are skipped rather than downloaded and shrunk.
MAX_REMOTE_IMAGE_BYTES = 8 * 1024 * 1024
PREVIEW_EXTENSIONS = ("png", "jpg", "jpeg", "gif")

# Search engines truncate descriptions around this length.
META_DESCRIPTION_LIMIT = 155

# Abort rather than publish if the repository count collapses; a partial API response must
# never wipe out the site. Expressed as the smallest acceptable fraction of the previous build.
MIN_REPO_RATIO = 0.7

# Year the site's copyright notice starts from.
COPYRIGHT_START_YEAR = 2026

API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
ALLOWED_HOSTS = {"api.github.com", "raw.githubusercontent.com"}
USER_AGENT = "EFDC-OpenSourceHub-SiteBuilder/1.0 (+https://code.depressioncenter.org/)"
HTTP_TIMEOUT_SECONDS = 30
HTTP_RETRIES = 4
# GitHub throttles bursts of unauthenticated requests from one address, so an anonymous run
# fetches one repository at a time. With a token the higher limits make parallelism safe.
MAX_WORKERS = 4
MAX_WORKERS_ANONYMOUS = 1

# The Open Source Hub is one shelf of a wider set of University of Michigan Health resources.
# An agent that finds only the code is missing the guidance, the publications, and the talks
# that go with it, so llms.txt points at all of them.
RESOURCE_LIBRARY = (
    (
        "Eisenberg Family Depression Center",
        "https://depressioncenter.org",
        "The Center itself: research programs, services, staff, and news.",
    ),
    (
        "EFDC Knowledge Base",
        "https://teamdynamix.umich.edu/TDClient/210/DepressionCenter/Home/",
        "Written guidance and how-to articles. The canonical documentation for most projects "
        "listed below.",
    ),
    (
        "GitHub organization",
        "https://github.com/DepressionCenter",
        "Source for every project, including issues, releases, and licences.",
    ),
    (
        "Video library",
        "https://www.youtube.com/user/DepressionCenter",
        "Recorded talks, demonstrations, and training sessions.",
    ),
)

# Relative output locations, all beneath the output directory.
LOCAL_PREVIEW_DIR = "images/repo-previews"
REMOTE_PREVIEW_DIR = "images/repo-previews/remote"
README_FRAGMENT_DIR = "data/readme"
CATALOG_PATH = "data/repos.json"
CACHE_PATH = "data/build-cache.json"
LLMS_TXT_PATH = "llms.txt"
FALLBACK_OG_IMAGE = "images/EFDCLogo_375w.png"

# Tags and attributes permitted in a README after GitHub has rendered it. Anything absent is
# removed. SVG is deliberately excluded: the only SVGs GitHub emits are the decorative icons
# inside note and warning callouts, and the callout text survives without them.
README_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "caption", "cite", "code", "col", "colgroup", "dd",
    "del", "details", "dfn", "div", "dl", "dt", "em", "figcaption", "figure", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "input", "ins", "kbd", "li", "mark", "ol", "p",
    "picture", "pre", "q", "rp", "rt", "ruby", "s", "samp", "small", "source", "span", "strong",
    "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "time", "tr", "ul",
    "var", "wbr",
}
README_ATTRIBUTES = {
    "*": {"class", "id", "dir", "title", "lang", "align"},
    # "rel" is omitted deliberately: link_rel below sets it, and nh3 refuses to do both.
    "a": {"href", "name", "target"},
    "blockquote": {"cite"},
    "col": {"span"},
    "colgroup": {"span"},
    "del": {"cite", "datetime"},
    "img": {"src", "alt", "width", "height", "loading", "srcset", "decoding"},
    "input": {"type", "checked", "disabled"},
    "ins": {"cite", "datetime"},
    "ol": {"start", "reversed", "type"},
    "q": {"cite"},
    "source": {"src", "srcset", "media", "type"},
    "td": {"colspan", "rowspan", "headers"},
    "th": {"colspan", "rowspan", "headers", "scope", "abbr"},
    "time": {"datetime"},
}
README_URL_SCHEMES = {"http", "https", "mailto"}

# Icons reused from the card and panel markup.
ICONS = {
    "github": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>',
    "web": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "demo": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    "docs": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
}

# Link buttons shown on cards, in display order: record key, visible label, icon, aria-label.
LINK_FIELDS = (
    ("repo_url", "Code", "github", "View {name} on GitHub"),
    ("website", "Website", "web", "{name} website"),
    ("demo", "Demo", "demo", "{name} demo"),
    ("docs", "Docs", "docs", "{name} documentation"),
)


class BuildError(RuntimeError):
    """A condition that must stop the build before anything is written to disk."""


### Retrieve Source Data ###


def _check_host(url):
    """Reject any URL outside the two GitHub hosts this build is allowed to contact.

    File paths used to construct download URLs come from the GitHub tree API, which is
    untrusted input. This keeps a crafted path from redirecting a request elsewhere.

    Args:
        url: The absolute URL about to be requested.

    Raises:
        BuildError: If the host is not on the allowlist.
    """
    host = urllib.parse.urlsplit(url).hostname
    if host not in ALLOWED_HOSTS:
        raise BuildError(f"Refusing to fetch from unexpected host: {host!r}")


def lowercase_headers(headers):
    """Normalize HTTP header names so lookups are not sensitive to their capitalization.

    HTTP/1.1 sends "X-RateLimit-Remaining" while HTTP/2 sends "x-ratelimit-remaining". A
    lookup that guesses wrong returns nothing and the caller silently mishandles the response.

    Args:
        headers: A header container from urllib, or None.

    Returns:
        dict[str, str]: The headers, keyed by lowercased name.
    """
    if not headers:
        return {}
    return {name.lower(): value for name, value in headers.items()}


def fetch(url, token, accept="application/vnd.github+json", etag=None):
    """Perform one HTTP GET against GitHub, with retries for transient failures.

    Args:
        url: Absolute URL on api.github.com or raw.githubusercontent.com.
        token: GitHub token, or None to make an unauthenticated request.
        accept: Value for the Accept header, which selects the API's response format.
        etag: Previous ETag, sent as If-None-Match so unchanged content returns 304.

    Returns:
        tuple[int, dict, bytes]: HTTP status, response headers, and the response body.
        Header names are lowercased, because HTTP/1.1 and HTTP/2 disagree on their
        capitalization and a case-sensitive lookup would silently miss.
        Status 304 and 404 are returned rather than raised; both are expected outcomes.

    Raises:
        BuildError: On rate-limit exhaustion, a persistent server error, or a network failure.
    """
    _check_host(url)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if etag:
        headers["If-None-Match"] = etag

    delay_seconds = 2
    for attempt in range(HTTP_RETRIES):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                return response.status, lowercase_headers(response.headers), response.read()
        except urllib.error.HTTPError as error:
            error_headers = lowercase_headers(error.headers)
            if error.code in (304, 404):
                return error.code, error_headers, b""
            if error.code in (403, 429):
                # The hourly quota is spent: waiting for it inside this run is not sensible.
                if error_headers.get("x-ratelimit-remaining") == "0":
                    reset = error_headers.get("x-ratelimit-reset", "")
                    when = ""
                    if reset.isdigit():
                        when = datetime.fromtimestamp(int(reset), timezone.utc).isoformat()
                    raise BuildError(
                        "GitHub API rate limit exhausted"
                        + (f"; resets at {when}" if when else "")
                        + ". Set GITHUB_TOKEN or GH_TOKEN to raise the limit from 60 to 1000 "
                        "requests an hour."
                    ) from error
                # Otherwise this is GitHub's secondary limit on bursts of requests, which
                # clears on its own. Honor Retry-After when GitHub sends one.
                if attempt < HTTP_RETRIES - 1:
                    retry_after = error_headers.get("retry-after", "")
                    wait = int(retry_after) if retry_after.isdigit() else delay_seconds
                    time.sleep(min(wait, 60))
                    delay_seconds *= 2
                    continue
                raise BuildError(
                    f"HTTP {error.code} for {url} after {HTTP_RETRIES} attempts. This is "
                    "GitHub's secondary rate limit; set GITHUB_TOKEN or GH_TOKEN, or rerun."
                ) from error
            if error.code >= 500 and attempt < HTTP_RETRIES - 1:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
            raise BuildError(f"HTTP {error.code} for {url}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt < HTTP_RETRIES - 1:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
            raise BuildError(f"Network failure for {url}: {error}") from error
    raise BuildError(f"Exhausted retries for {url}")


def fetch_json(url, token):
    """Fetch a URL and parse the response as JSON.

    Args:
        url: Absolute API URL.
        token: GitHub token, or None.

    Returns:
        tuple[object, dict]: The decoded JSON body and the response headers.

    Raises:
        BuildError: If the response is not a 200 or the body is not valid JSON.
    """
    status, headers, body = fetch(url, token)
    if status != 200:
        raise BuildError(f"Unexpected status {status} for {url}")
    try:
        return json.loads(body.decode("utf-8")), headers
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BuildError(f"Malformed JSON from {url}: {error}") from error


def next_page_url(link_header):
    """Extract the next page URL from a GitHub Link header.

    Args:
        link_header: Raw value of the Link response header, possibly empty.

    Returns:
        str | None: The URL marked rel="next", or None when this is the last page.
    """
    for part in (link_header or "").split(","):
        match = re.match(r'\s*<([^>]+)>\s*;\s*rel="next"', part)
        if match:
            return match.group(1)
    return None


def fetch_org_repositories(token):
    """Fetch every repository in the organization, following pagination.

    Args:
        token: GitHub token, or None.

    Returns:
        list[dict]: Raw repository objects as returned by the API.
    """
    url = f"{API_ROOT}/orgs/{ORG}/repos?per_page=100&sort=full_name"
    repositories = []
    while url:
        page, headers = fetch_json(url, token)
        if not isinstance(page, list):
            raise BuildError(f"Expected a list of repositories from {url}")
        repositories.extend(page)
        url = next_page_url(headers.get("link"))
    return repositories


def fetch_readme_html(slug, token, etag):
    """Fetch a repository README already rendered to HTML by GitHub.

    Using GitHub's own renderer keeps the site's Markdown handling identical to what readers
    see on GitHub, and means relative image paths arrive already resolved.

    Args:
        slug: Repository name.
        token: GitHub token, or None.
        etag: ETag from the previous build, or None.

    Returns:
        tuple[str | None, str | None]: The rendered HTML and its new ETag. The HTML is None
        when the content is unchanged (304) or the repository has no README (404).
    """
    status, headers, body = fetch(
        f"{API_ROOT}/repos/{ORG}/{urllib.parse.quote(slug)}/readme",
        token,
        accept="application/vnd.github.html+json",
        etag=etag,
    )
    if status == 304:
        return None, etag
    if status == 404:
        return None, None
    return body.decode("utf-8", errors="replace"), headers.get("etag")


def fetch_tree(slug, branch, token):
    """List every file in a repository at its default branch.

    Args:
        slug: Repository name.
        branch: Default branch name.
        token: GitHub token, or None.

    Returns:
        dict[str, dict]: Blob entries keyed by lowercased path, each with path, sha, and size.
        Empty when the repository has no files or the tree could not be read.
    """
    url = (
        f"{API_ROOT}/repos/{ORG}/{urllib.parse.quote(slug)}/git/trees/"
        f"{urllib.parse.quote(branch)}?recursive=1"
    )
    status, _, body = fetch(url, token)
    if status != 200:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return {
        entry["path"].lower(): entry
        for entry in payload.get("tree", [])
        if entry.get("type") == "blob" and "path" in entry
    }


### Transform Records ###


def safe_url(value):
    """Return a URL only if it uses a scheme safe to place in an href.

    Repository homepages and custom properties are set by repository owners, so a value such
    as "javascript:..." must never reach the page.

    Args:
        value: Candidate URL, possibly None or empty.

    Returns:
        str: The URL, or an empty string when it is missing or uses another scheme.
    """
    text = (value or "").strip()
    if not text:
        return ""
    scheme = urllib.parse.urlsplit(text).scheme.lower()
    return text if scheme in ("http", "https") else ""


def esc(value):
    """HTML-escape a value for use in text or in a quoted attribute.

    Args:
        value: Any value; None becomes an empty string.

    Returns:
        str: The escaped text.
    """
    return html.escape("" if value is None else str(value), quote=True)


def monogram(name):
    """Build the two-letter initials shown when a repository has no preview image.

    Args:
        name: Repository name.

    Returns:
        str: Up to two uppercase characters.
    """
    words = re.sub(r"[^A-Za-z0-9]", " ", re.sub(r"[™®]", "", name)).split()
    return "".join(word[0] for word in words[:2]).upper()


def build_tags(language, topics):
    """Combine a repository's language and topics into the tag list shown on its card.

    Args:
        language: Primary language reported by GitHub, possibly None.
        topics: List of repository topics, possibly empty.

    Returns:
        list[str]: Unique tags in display order, capped at MAX_TAGS.
    """
    tags = []
    seen = set()
    for tag in [language] + list(topics or []):
        if not tag:
            continue
        key = tag.lower()
        if key in IGNORE_TOPICS or key in seen:
            continue
        seen.add(key)
        tags.append(tag)
    return tags[:MAX_TAGS]


def to_record(api_repo):
    """Reduce a GitHub repository object to the fields the site actually renders.

    Custom properties are set per repository in the organization's settings. "featured" is a
    string there, not a boolean, so it is compared as text.

    Args:
        api_repo: One repository object from the API.

    Returns:
        dict: A repository record used by every render function below.
    """
    properties = api_repo.get("custom_properties") or {}
    license_info = api_repo.get("license") or {}
    name = api_repo["name"]

    return {
        "slug": name,
        "name": name,
        "description": (api_repo.get("description") or "").strip(),
        "repo_url": safe_url(api_repo.get("html_url")),
        "website": safe_url(api_repo.get("homepage")),
        "demo": safe_url(properties.get("demo_url")),
        "docs": safe_url(properties.get("docs_url")),
        "lab_name": (properties.get("lab_name") or "").strip(),
        "lab_url": safe_url(properties.get("lab_url")),
        "language": api_repo.get("language") or "",
        "topics": api_repo.get("topics") or [],
        "tags": build_tags(api_repo.get("language"), api_repo.get("topics")),
        "featured": str(properties.get("featured", "")).strip().lower() == "true",
        "pushed_at": api_repo.get("pushed_at") or "",
        "default_branch": api_repo.get("default_branch") or "main",
        "license": license_info.get("spdx_id") or "",
        "monogram": monogram(name),
        "full_image": "",
        "thumb_image": "",
        "image_source": "placeholder",
    }


### Transform Records: README markup ###

README_WRAPPER_RE = re.compile(
    r'^\s*<div id="readme".*?>\s*<article[^>]*>(.*)</article>\s*</div>\s*$', re.S | re.I
)
LOGO_ANCHOR_RE = re.compile(r"<a[^>]*>\s*<img[^>]*EFDCLogo_375w\.png[^>]*>\s*</a>", re.I)
LOGO_IMG_RE = re.compile(r"<img[^>]*EFDCLogo_375w\.png[^>]*>", re.I)
EMPTY_PARAGRAPH_RE = re.compile(r"<p[^>]*>\s*</p>", re.I)
EMPTY_ANCHOR_RE = re.compile(r'<a[^>]*class="[^"]*anchor[^"]*"[^>]*>\s*</a>', re.I)
EXTERNAL_ANCHOR_RE = re.compile(
    r'<a\s+(?![^>]*\btarget=)([^>]*href="https?://[^"]*"[^>]*)>', re.I
)


def demote_headings(markup):
    """Shift every heading in a README down one level.

    The page supplies its own H1 (the repository name), and a document must have only one, so
    the README's own H1 becomes an H2 and so on. H6 has nowhere to go and is left alone.

    Args:
        markup: Sanitized HTML.

    Returns:
        str: The same HTML with heading levels shifted.
    """
    for level in range(5, 0, -1):
        markup = re.sub(rf"<h{level}(\s|>)", rf"<h{level + 1}\1", markup, flags=re.I)
        markup = re.sub(rf"</h{level}>", f"</h{level + 1}>", markup, flags=re.I)
    return markup


RELATIVE_URL_ATTRIBUTE_RE = re.compile(r'\b(src|href)="([^"]*)"')
ABSOLUTE_URL_PREFIXES = ("http://", "https://", "mailto:", "data:", "#", "//")


def absolutize_readme_links(markup, slug, branch):
    """Point a README's relative links and images at the repository they came from.

    GitHub rewrites Markdown image syntax to absolute proxy URLs when it renders a README, but
    it leaves raw HTML tags alone. A README written with <img src="images/screenshot.png">
    therefore arrives with a path that means nothing once the markup is shown on this site.

    A path starting with "/" is treated as relative to the repository root as well. Read
    literally it would mean the root of github.com, where nothing useful lives, so the author
    can only have meant the repository.

    Args:
        markup: Sanitized README HTML.
        slug: Repository the README belongs to.
        branch: Branch the README was read from.

    Returns:
        str: The same markup with relative references made absolute.
    """
    quoted_slug = urllib.parse.quote(slug)
    quoted_branch = urllib.parse.quote(branch)
    raw_base = f"{RAW_ROOT}/{ORG}/{quoted_slug}/{quoted_branch}/"
    blob_base = f"https://github.com/{ORG}/{quoted_slug}/blob/{quoted_branch}/"
    tree_base = f"https://github.com/{ORG}/{quoted_slug}/tree/{quoted_branch}/"

    def rewrite(match):
        attribute, value = match.group(1), match.group(2)
        if not value or value.startswith(ABSOLUTE_URL_PREFIXES):
            return match.group(0)

        path = value
        while path.startswith("./"):
            path = path[2:]
        path = path.lstrip("/")
        # A path climbing above the repository root has no sensible target; leave it alone
        # rather than inventing one.
        if not path or path.startswith("../"):
            return match.group(0)

        # Images are served from the raw file host; links go to the rendered view on GitHub,
        # which needs to know whether the target is a file or a directory.
        if attribute == "src":
            base = raw_base
        else:
            last_segment = path.rstrip("/").rsplit("/", 1)[-1]
            base = blob_base if "." in last_segment else tree_base
        return f'{attribute}="{base}{path}"'

    return RELATIVE_URL_ATTRIBUTE_RE.sub(rewrite, markup)


def process_readme(rendered_html, slug, branch):
    """Turn GitHub's rendered README into markup safe to embed in this site.

    GitHub sanitizes what it renders; this repeats the work with an explicit allowlist because
    content fetched at runtime is untrusted no matter who rendered it.

    Args:
        rendered_html: HTML as returned by the README endpoint.
        slug: Repository the README belongs to, used to resolve relative links.
        branch: Branch the README was read from.

    Returns:
        str: Sanitized HTML with headings demoted and external links opening in a new tab.
    """
    markup = rendered_html or ""

    # Drop GitHub's own page furniture so only the README body remains.
    wrapper = README_WRAPPER_RE.match(markup)
    if wrapper:
        markup = wrapper.group(1)

    # Each README opens with the Center's logo, which would duplicate the header on this site.
    markup = LOGO_ANCHOR_RE.sub("", markup)
    markup = LOGO_IMG_RE.sub("", markup)

    markup = nh3.clean(
        markup,
        tags=README_TAGS,
        attributes=README_ATTRIBUTES,
        url_schemes=README_URL_SCHEMES,
        link_rel="nofollow noopener noreferrer",
    )

    # GitHub prefixes each heading with an empty anchor holding an icon that did not survive
    # sanitizing, and removing the logo can leave an empty paragraph behind.
    markup = EMPTY_ANCHOR_RE.sub("", markup)
    markup = EMPTY_PARAGRAPH_RE.sub("", markup)
    markup = absolutize_readme_links(markup, slug, branch)
    markup = demote_headings(markup)

    # Links to other sites open in a new tab, matching how the panel behaved previously.
    # In-page anchors are left alone so a table of contents still scrolls the same page.
    markup = EXTERNAL_ANCHOR_RE.sub(r'<a target="_blank" \1>', markup)
    return markup.strip()


### Transform Records: preview images ###


def preview_candidates(slug, want_thumb):
    """List the file paths that may hold a repository's own preview image, best first.

    The naming convention comes from the EFDC repository template; the repository-name variants
    match how preview images were named by hand before that template existed.

    Args:
        slug: Repository name.
        want_thumb: True to look for thumbnail names, False for full-size names.

    Returns:
        list[str]: Lowercased candidate paths in priority order.
    """
    suffix = "-thumb" if want_thumb else ""
    paths = []
    for stem in (f"repo-preview{suffix}", f"{slug.lower()}{suffix}"):
        for folder in ("images/", ""):
            for extension in PREVIEW_EXTENSIONS:
                paths.append(f"{folder}{stem}.{extension}")
    return paths


def pick_candidate(tree, slug, want_thumb, placeholder_shas):
    """Choose which file in a repository to use as its preview image.

    Args:
        tree: Blob entries keyed by lowercased path.
        slug: Repository name.
        want_thumb: True for the thumbnail, False for the full-size image.
        placeholder_shas: Blob hashes of the untouched template placeholders.

    Returns:
        dict | None: The chosen tree entry, or None when nothing usable was found. A file
        whose contents match the template placeholder is treated as absent, because it means
        the repository never replaced the template's stand-in image.
    """
    for path in preview_candidates(slug, want_thumb):
        entry = tree.get(path)
        if not entry:
            continue
        if entry.get("sha") in placeholder_shas:
            continue
        if (entry.get("size") or 0) > MAX_REMOTE_IMAGE_BYTES:
            continue
        return entry
    return None


def download_image(slug, branch, path, token):
    """Download one image file from a repository.

    Args:
        slug: Repository name.
        branch: Branch to read from.
        path: File path within the repository, with its original capitalization.
        token: GitHub token, or None.

    Returns:
        bytes | None: The file contents, or None when it could not be fetched.
    """
    quoted = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    url = f"{RAW_ROOT}/{ORG}/{urllib.parse.quote(slug)}/{urllib.parse.quote(branch)}/{quoted}"
    status, _, body = fetch(url, token)
    if status != 200 or not body:
        return None
    return body


def write_preview(data, destination, max_width):
    """Normalize downloaded image bytes and write them as a PNG.

    Args:
        data: Raw image file contents.
        destination: Path to write.
        max_width: Largest width to produce.

    Returns:
        bool: True when the image was written, False when it could not be decoded.
    """
    try:
        with Image.open(io.BytesIO(data)) as image:
            flattened = flatten_for_png(image)
            save_png(normalize_preview(flattened, max_width), destination)
        return True
    except Exception as error:  # Pillow raises several types for malformed or oversized input
        print(f"    could not process image: {error}")
        return False


def resolve_images(record, tree, placeholder_shas, token, output_root, cache_entry):
    """Decide which preview images a repository gets, downloading them when needed.

    Precedence, first match wins: the repository's own preview image, then the hand-made
    thumbnail kept in this repository, then the initials placeholder drawn in CSS.

    Args:
        record: Repository record, updated in place.
        tree: Blob entries for the repository, keyed by lowercased path.
        placeholder_shas: Blob hashes of the untouched template placeholders.
        token: GitHub token, or None.
        output_root: Directory the site is being written to.
        cache_entry: Previous build's cache for this repository, updated in place.
    """
    slug = record["slug"]
    full_entry = pick_candidate(tree, slug, False, placeholder_shas)
    thumb_entry = pick_candidate(tree, slug, True, placeholder_shas)

    if full_entry or thumb_entry:
        full_relative = f"{REMOTE_PREVIEW_DIR}/{slug}.png"
        thumb_relative = f"{REMOTE_PREVIEW_DIR}/{slug}-thumb.png"
        full_path = output_root / full_relative
        thumb_path = output_root / thumb_relative

        # A git blob hash identifies file contents, so an unchanged image is never re-fetched.
        source_entry = full_entry or thumb_entry
        source_sha = source_entry["sha"]
        thumb_sha = (thumb_entry or full_entry)["sha"]
        already_current = (
            cache_entry.get("image_sha") == source_sha
            and cache_entry.get("thumb_sha") == thumb_sha
            and full_path.exists()
            and thumb_path.exists()
        )

        if already_current:
            record.update(
                full_image=full_relative, thumb_image=thumb_relative, image_source="remote"
            )
            return

        full_data = download_image(slug, record["default_branch"], source_entry["path"], token)
        thumb_data = full_data
        if thumb_entry is not None and thumb_entry is not source_entry:
            thumb_data = (
                download_image(slug, record["default_branch"], thumb_entry["path"], token)
                or full_data
            )

        wrote_full = bool(full_data) and write_preview(full_data, full_path, FULL_MAX_WIDTH)
        wrote_thumb = bool(thumb_data) and write_preview(thumb_data, thumb_path, THUMB_MAX_WIDTH)
        if wrote_full and wrote_thumb:
            cache_entry["image_sha"] = source_sha
            cache_entry["thumb_sha"] = thumb_sha
            record.update(
                full_image=full_relative, thumb_image=thumb_relative, image_source="remote"
            )
            return

    # No usable image in the repository: fall back to the thumbnails maintained here.
    cache_entry.pop("image_sha", None)
    cache_entry.pop("thumb_sha", None)
    local_full = f"{LOCAL_PREVIEW_DIR}/{slug}.png"
    local_thumb = f"{LOCAL_PREVIEW_DIR}/{slug}-thumb.png"
    if (ROOT / local_full).exists() and (ROOT / local_thumb).exists():
        record.update(full_image=local_full, thumb_image=local_thumb, image_source="local")


### Transform Records: HTML fragments ###


def render_links(record):
    """Build the row of Code, Website, Demo, and Docs buttons for one repository.

    Args:
        record: Repository record.

    Returns:
        str: HTML for the links present on this repository; empty when it has none.
    """
    parts = []
    for key, label, icon, aria_template in LINK_FIELDS:
        url = record.get(key)
        if not url:
            continue
        aria = aria_template.format(name=record["name"])
        parts.append(
            f'<a class="repo-link" href="{esc(url)}" target="_blank" rel="noopener" '
            f'aria-label="{esc(aria)}">{ICONS[icon]} {label}</a>'
        )
    return "".join(parts)


def render_tags(record, interactive):
    """Build the tag chips for one repository.

    Args:
        record: Repository record.
        interactive: True on the landing page, where a tag filters the grid and must therefore
            be a real button. False on a detail page, where there is nothing to filter and a
            control that does nothing would mislead keyboard and screen reader users.

    Returns:
        str: HTML for the tags.
    """
    parts = []
    for tag in record["tags"]:
        if interactive:
            parts.append(
                f'<button type="button" class="lang-tag" data-tag="{esc(tag)}">'
                f"{esc(tag)}</button>"
            )
        else:
            parts.append(f'<span class="lang-tag">{esc(tag)}</span>')
    return "".join(parts)


def render_thumb(record, path_prefix, css_class):
    """Build a repository's preview image, or its initials when it has none.

    The result is marked decorative: the repository name sits next to it as real text, so
    announcing the image as well would only repeat that name.

    Args:
        record: Repository record.
        path_prefix: Prefix that makes image paths resolve from the calling page.
        css_class: Base class controlling the box size.

    Returns:
        str: HTML for the preview box.
    """
    if record["thumb_image"]:
        inner = (
            f'<img src="{esc(path_prefix + record["thumb_image"])}" alt="" '
            f'loading="lazy" decoding="async" />'
        )
    else:
        inner = (
            '<div class="thumb-placeholder">'
            f'<span class="thumb-monogram">{esc(record["monogram"])}</span></div>'
        )
    return (
        f'<div class="{css_class} card-panel-trigger" data-slug="{esc(record["slug"])}" '
        f'aria-hidden="true">{inner}</div>'
    )


def search_text(record):
    """Build the lowercased text the client-side search box matches against.

    Keeping this on the card removes any need to fetch a separate index at page load.

    Args:
        record: Repository record.

    Returns:
        str: Space-separated searchable text.
    """
    parts = [record["name"], record["slug"], record["description"], record["language"]]
    parts.extend(record["topics"])
    return " ".join(part for part in parts if part).lower()


def detail_url(slug, absolute=False):
    """Build the URL of a repository's detail page.

    Args:
        slug: Repository name.
        absolute: True for a full URL, False for one relative to the site root.

    Returns:
        str: The URL, always ending in a slash so the page is served as a directory index.
    """
    path = f"{DETAIL_PATH_PREFIX}/{urllib.parse.quote(slug)}/"
    return f"{SITE_BASE_URL}/{path}" if absolute else path


def render_card(record, featured):
    """Build one repository card for the landing page.

    The title is the card's only tab stop and is a real link, so the page works without
    JavaScript; the script upgrades the click into the slide-in panel.

    Args:
        record: Repository record.
        featured: True to render the larger featured card.

    Returns:
        str: HTML for one card.
    """
    slug = esc(record["slug"])
    href = esc(detail_url(record["slug"]))
    title_link = (
        f'<a class="card-title-link card-panel-trigger" href="{href}" data-slug="{slug}">'
        f'{esc(record["name"])}</a>'
    )
    description = esc(record["description"]) or "No description available."
    body = (
        f'<p class="card-panel-trigger" data-slug="{slug}">{description}</p>\n'
        f'          <div class="repo-meta">{render_tags(record, True)}</div>\n'
        f'          <div class="repo-links">{render_links(record)}</div>'
    )

    repo_attribute = f' data-repo-url="{esc(record["repo_url"])}"' if record["repo_url"] else ""

    if featured:
        return (
            f'        <article class="featured-card" role="listitem"{repo_attribute} '
            f'data-search="{esc(search_text(record))}">\n'
            f'          {render_thumb(record, "", "featured-thumb")}\n'
            f'          <span class="featured-badge" aria-hidden="true">Featured</span>\n'
            f'          <div class="featured-body">\n'
            f"            <h3>{title_link}</h3>\n"
            f"            {body}\n"
            f"          </div>\n"
            f"        </article>"
        )
    return (
        f'        <article class="repo-card" role="listitem"{repo_attribute} '
        f'data-search="{esc(search_text(record))}">\n'
        f"          <h3>{title_link}</h3>\n"
        f'          {render_thumb(record, "", "featured-thumb")}\n'
        f"          {body}\n"
        f"        </article>"
    )


def render_lab(record, indent=""):
    """Build the "Lab/Team" line shown above a repository's links.

    Args:
        record: Repository record.
        indent: Leading whitespace, so generated pages stay readable when viewed as source.

    Returns:
        str: HTML for the line, or an empty string when no lab is recorded.
    """
    if not record["lab_name"]:
        return ""
    lab_name = esc(record["lab_name"])
    inner = (
        f'<a href="{esc(record["lab_url"])}" target="_blank" rel="noopener">{lab_name}</a>'
        if record["lab_url"]
        else lab_name
    )
    return (
        f'{indent}<div class="panel-lab"><span class="panel-lab-label">Lab/Team:</span> '
        f"{inner}</div>"
    )


def render_preview_box(record, path_prefix, extra_class=""):
    """Build the large preview image used by the panel and the detail pages.

    Args:
        record: Repository record.
        path_prefix: Prefix that makes the image path resolve from the calling page.
        extra_class: Additional CSS class for the wrapper.

    Returns:
        str: HTML for the preview box.
    """
    if record["full_image"]:
        inner = f'<img src="{esc(path_prefix + record["full_image"])}" alt="" loading="lazy" />'
    else:
        inner = (
            '<div class="thumb-placeholder">'
            f'<span class="thumb-monogram">{esc(record["monogram"])}</span></div>'
        )
    classes = f"panel-thumb-lg {extra_class}".strip()
    return f'<div class="{classes}" aria-hidden="true">{inner}</div>'


def render_panel_fragment(record, readme_html):
    """Build the panel body the landing page loads when a card is clicked.

    This is the same content as the detail page, so the two can never disagree. Paths resolve
    from the site root because the panel only exists on the landing page.

    Args:
        record: Repository record.
        readme_html: Sanitized README markup, possibly empty.

    Returns:
        str: HTML for the panel body.
    """
    body = readme_html or f"<p>{esc(record['description']) or 'No description available.'}</p>"
    links = render_links(record)
    return (
        f"{render_preview_box(record, '')}\n"
        f"{render_lab(record)}\n"
        f'<div class="repo-links">{links}</div>\n'
        f'<div class="panel-readme">{body}</div>\n'
        f'<div class="repo-links panel-links-bottom">{links}</div>\n'
    )


### Transform Records: page metadata ###


def meta_description(text):
    """Trim a description to a length search engines will display in full.

    Args:
        text: Repository description, possibly empty.

    Returns:
        str: The description, cut at a word boundary and ellipsized when too long.
    """
    text = " ".join((text or "").split())
    if len(text) <= META_DESCRIPTION_LIMIT:
        return text
    return text[:META_DESCRIPTION_LIMIT].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def render_head_meta(title, description, canonical, image_url, og_type):
    """Build the title, description, canonical link, and social sharing tags for a page.

    Args:
        title: Page title.
        description: Plain-language summary, already trimmed.
        canonical: Absolute URL of this page.
        image_url: Absolute URL of the sharing image.
        og_type: Open Graph type, "website" for the landing page or "article" for a repository.

    Returns:
        str: HTML for the head of the page.
    """
    return "\n".join(
        [
            f"  <title>{esc(title)}</title>",
            f'  <meta name="description" content="{esc(description)}" />',
            f'  <link rel="canonical" href="{esc(canonical)}" />',
            f'  <meta property="og:type" content="{esc(og_type)}" />',
            '  <meta property="og:site_name" content="EFDC Open Source Hub" />',
            f'  <meta property="og:title" content="{esc(title)}" />',
            f'  <meta property="og:description" content="{esc(description)}" />',
            f'  <meta property="og:url" content="{esc(canonical)}" />',
            f'  <meta property="og:image" content="{esc(image_url)}" />',
            '  <meta name="twitter:card" content="summary_large_image" />',
            f'  <meta name="twitter:title" content="{esc(title)}" />',
            f'  <meta name="twitter:description" content="{esc(description)}" />',
            f'  <meta name="twitter:image" content="{esc(image_url)}" />',
        ]
    )


def render_jsonld(payload):
    """Serialize structured data into a script tag.

    Args:
        payload: A JSON-serializable object following schema.org.

    Returns:
        str: A script element carrying the data.
    """
    # Escaping "<" keeps a description containing "</script>" from ending the element early.
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
    return f'  <script type="application/ld+json">{text}</script>'


def absolute_image_url(record):
    """Build the absolute URL of the image used when a page is shared on social media.

    Args:
        record: Repository record.

    Returns:
        str: An absolute URL, falling back to the Center's logo when there is no preview.
    """
    return f"{SITE_BASE_URL}/{record['full_image'] or FALLBACK_OG_IMAGE}"


def copyright_years():
    """Build the year range shown in the footer.

    Returns:
        str: A single year while the site is in its first year, a range afterwards.
    """
    current = datetime.now(timezone.utc).year
    if current <= COPYRIGHT_START_YEAR:
        return str(COPYRIGHT_START_YEAR)
    return f"{COPYRIGHT_START_YEAR}-{current}"


### Save Results ###


GENERATED_NOTICE = (
    "<!-- Generated by scripts/build_site.py. Do not edit this file: the next build replaces"
    " it. Edit templates/, styles/site.css, or scripts/site.js instead. -->"
)


def mark_generated(markup):
    """Add a notice telling a reader that editing this file by hand accomplishes nothing.

    Args:
        markup: A finished HTML page beginning with its doctype.

    Returns:
        str: The same page with the notice immediately after the doctype.
    """
    marker = "<!DOCTYPE html>"
    if markup.startswith(marker):
        return f"{marker}\n{GENERATED_NOTICE}{markup[len(marker):]}"
    return f"{GENERATED_NOTICE}\n{markup}"


def fill(template, values):
    """Substitute placeholder tokens in a template.

    Args:
        template: Template text containing tokens such as REPO_NAME in double braces.
        values: Mapping of token name to replacement HTML.

    Returns:
        str: The filled template.

    Raises:
        BuildError: If any token remains unfilled, which would publish a broken page.
    """
    output = template
    for key, value in values.items():
        output = output.replace("{{" + key + "}}", value)
    leftover = sorted(set(re.findall(r"\{\{([A-Z_]+)\}\}", output)))
    if leftover:
        raise BuildError(f"Template still contains unfilled tokens: {leftover}")
    return output


def render_index(template, records):
    """Build the landing page.

    Args:
        template: Contents of templates/index.html.
        records: All repository records, in display order.

    Returns:
        str: The finished HTML.
    """
    featured = [record for record in records if record["featured"]]
    featured_html = "\n".join(render_card(record, True) for record in featured) or (
        '        <p class="error-state">No featured repositories found.</p>'
    )
    count = len(records)
    newest = max((record["pushed_at"] for record in records if record["pushed_at"]), default="")

    jsonld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": SITE_TITLE,
        "description": SITE_DESCRIPTION,
        "url": f"{SITE_BASE_URL}/",
        "dateModified": newest,
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": count,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index + 1,
                    "name": record["name"],
                    "url": detail_url(record["slug"], absolute=True),
                }
                for index, record in enumerate(records)
            ],
        },
    }

    return fill(
        template,
        {
            "HEAD_META": render_head_meta(
                SITE_TITLE,
                SITE_DESCRIPTION,
                f"{SITE_BASE_URL}/",
                f"{SITE_BASE_URL}/{FALLBACK_OG_IMAGE}",
                "website",
            ),
            "JSONLD": render_jsonld(jsonld),
            "FEATURED_CARDS": featured_html,
            "REPO_CARDS": "\n".join(render_card(record, False) for record in records),
            "REPO_COUNT": str(count),
            "REPO_COUNT_LABEL": f"{count} repo{'s' if count != 1 else ''}",
            "COPYRIGHT_YEAR": copyright_years(),
        },
    )


def render_detail_page(template, record, readme_html):
    """Build one repository's detail page.

    Args:
        template: Contents of templates/repo.html.
        record: Repository record.
        readme_html: Sanitized README markup, possibly empty.

    Returns:
        str: The finished HTML.
    """
    canonical = detail_url(record["slug"], absolute=True)
    description = meta_description(record["description"]) or (
        f"{record['name']} is an open source project from the Eisenberg Family "
        "Depression Center."
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": record["name"],
        "description": record["description"] or description,
        "url": canonical,
        "codeRepository": record["repo_url"],
        "image": absolute_image_url(record),
        "author": {
            "@type": "Organization",
            "name": "Eisenberg Family Depression Center",
            "url": "https://depressioncenter.org",
        },
        "isPartOf": {"@type": "CollectionPage", "url": f"{SITE_BASE_URL}/"},
    }
    if record["language"]:
        jsonld["programmingLanguage"] = record["language"]
    if record["license"] and record["license"] != "NOASSERTION":
        jsonld["license"] = record["license"]
    if record["pushed_at"]:
        jsonld["dateModified"] = record["pushed_at"]
    if record["tags"]:
        jsonld["keywords"] = ", ".join(record["tags"])

    body = readme_html or f"<p>{esc(record['description']) or 'No description available.'}</p>"

    return fill(
        template,
        {
            "HEAD_META": render_head_meta(
                f"{record['name']} | EFDC Open Source Hub",
                description,
                canonical,
                absolute_image_url(record),
                "article",
            ),
            "JSONLD": render_jsonld(jsonld),
            "REPO_NAME": esc(record["name"]),
            "DESCRIPTION": esc(record["description"]) or "No description available.",
            "PREVIEW": "      " + render_preview_box(record, "../../", "detail-thumb"),
            "LAB": render_lab(record, indent="      "),
            "LINKS": render_links(record),
            "TAGS": render_tags(record, False),
            "README_HTML": body,
            "COPYRIGHT_YEAR": copyright_years(),
        },
    )


def markdown_text(value):
    """Flatten a value into something safe to place inside a Markdown link description.

    A repository description can contain line breaks and square brackets, either of which
    would break the surrounding link syntax.

    Args:
        value: Any text, possibly empty or spanning several lines.

    Returns:
        str: Single-line text with link punctuation escaped.
    """
    text = " ".join((value or "").split())
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def render_repository_entry(record):
    """Describe one repository as a Markdown list item for llms.txt.

    The primary link is this site's page for the repository, because that page carries the
    full README as plain text. The source, documentation, demo, and project site follow as
    secondary links so an agent can go straight to whichever it needs.

    Args:
        record: Repository record.

    Returns:
        str: One Markdown list item.
    """
    description = markdown_text(record["description"]) or "No description provided."
    extras = []
    seen_urls = set()
    for key, label in (
        ("repo_url", "source"),
        ("docs", "documentation"),
        ("demo", "live demo"),
        ("website", "project site"),
    ):
        url = record.get(key)
        # Several repositories point their documentation and homepage at the same page;
        # listing it twice tells a reader nothing and wastes their attention.
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        extras.append(f"[{label}]({url})")

    line = f"- [{markdown_text(record['name'])}]({detail_url(record['slug'], absolute=True)}): {description}"
    if record["language"]:
        line += f" Primary language: {markdown_text(record['language'])}."
    if extras:
        line += " Links: " + ", ".join(extras) + "."
    return line


def render_llms_txt(records):
    """Build llms.txt, a plain-text map of this site for language models and agents.

    Follows the llmstxt.org convention: a title, a summary blockquote, then sections of
    Markdown links. Regenerated on every build, so it cannot drift from the site.

    Args:
        records: All repository records, in display order.

    Returns:
        str: The finished llms.txt.
    """
    featured = [record for record in records if record["featured"]]
    others = [record for record in records if not record["featured"]]

    lines = [
        "# EFDC Open Source Hub",
        "",
        "> Open source research and automation code published by the Eisenberg Family "
        "Depression Center at the University of Michigan. Tools for mental health research "
        "that are written to be reused across any research discipline.",
        "",
        "This file is generated automatically from the GitHub organization and is rebuilt "
        "nightly. It lists every public repository with its documentation and demos.",
        "",
        "## How to use this collection",
        "",
        "Treat this site as one part of a larger University of Michigan Health research "
        "resource library rather than a standalone code index. Each project usually has "
        "written guidance in the Knowledge Base and sometimes a recorded demonstration, and "
        "those explain the research context that the source code alone does not. When "
        "answering a question about any project below, check the companion resources:",
        "",
    ]
    for name, url, description in RESOURCE_LIBRARY:
        lines.append(f"- [{name}]({url}): {description}")

    lines += [
        "",
        "Each repository below has a page on this site holding its full README as readable "
        "text. Those pages are the fastest way to read a project's documentation, and they "
        "are listed in [the sitemap](" + SITE_BASE_URL + "/sitemap.xml). A machine-readable "
        "version of this catalog, including which preview image each project uses, is at "
        "[data/repos.json](" + SITE_BASE_URL + "/data/repos.json).",
        "",
        "All code is published under the GNU General Public License v3.0 or later unless a "
        "repository states otherwise. Please cite the repository you use.",
        "",
    ]

    if featured:
        lines += [
            "## Featured projects",
            "",
            "Projects the Center currently highlights. Start here when a question is general "
            "rather than about a specific tool.",
            "",
        ]
        lines.extend(render_repository_entry(record) for record in featured)
        lines.append("")

    lines += [
        "## All repositories",
        "",
    ]
    lines.extend(render_repository_entry(record) for record in others)

    lines += [
        "",
        "## Optional",
        "",
        "- [Community open source tools](" + SITE_BASE_URL + "/#community-oss): a curated "
        "list of open source projects from outside this organization that are useful in "
        "mental health and mobile technology research.",
        "- [Michigan Open Source Support (MOSS)](https://innovationpartnerships.umich.edu/moss/): "
        "the University of Michigan program for publishing open source software.",
        "- [MTC Code Publishing Service](https://teamdynamix.umich.edu/TDClient/210/DepressionCenter/KB/Article/13448/MTC-Code-Publishing-Service): "
        "a free service helping U-M research teams generalize and publish their code.",
        "",
    ]
    return "\n".join(lines)


def render_sitemap(records):
    """Build sitemap.xml covering the landing page and every repository page.

    Args:
        records: All repository records.

    Returns:
        str: The sitemap XML.
    """
    newest = max((record["pushed_at"] for record in records if record["pushed_at"]), default="")
    entries = [(f"{SITE_BASE_URL}/", newest, "1.0")]
    entries.extend(
        (detail_url(record["slug"], absolute=True), record["pushed_at"], "0.8")
        for record in records
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- Generated by scripts/build_site.py. Do not edit. -->",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, lastmod, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{esc(url)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{esc(lastmod)}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write_text(path, text):
    """Write UTF-8 text with Unix line endings, creating parent folders as needed.

    Args:
        path: Destination path.
        text: File contents.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def prune_stale(output_root, slugs):
    """Delete generated files belonging to repositories that no longer exist.

    Args:
        output_root: Directory the site was written to.
        slugs: Repository names in the current build.
    """
    detail_root = output_root / DETAIL_PATH_PREFIX
    if detail_root.is_dir():
        for child in sorted(detail_root.iterdir()):
            if child.is_dir() and child.name not in slugs:
                shutil.rmtree(child)
                print(f"  removed stale page {child.name}")

    fragment_root = output_root / README_FRAGMENT_DIR
    if fragment_root.is_dir():
        for child in sorted(fragment_root.glob("*.html")):
            if child.stem not in slugs:
                child.unlink()
                print(f"  removed stale fragment {child.name}")

    remote_root = output_root / REMOTE_PREVIEW_DIR
    if remote_root.is_dir():
        for child in sorted(remote_root.glob("*.png")):
            stem = child.stem[: -len("-thumb")] if child.stem.endswith("-thumb") else child.stem
            if stem not in slugs:
                child.unlink()
                print(f"  removed stale image {child.name}")


def load_cache(output_root):
    """Read the previous build's cache.

    Args:
        output_root: Directory the site is written to.

    Returns:
        dict: The cache, or an empty structure when there is none or it cannot be read.
    """
    path = output_root / CACHE_PATH
    if not path.exists():
        return {"version": 1, "repo_count": 0, "repos": {}}
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
        cache.setdefault("repos", {})
        cache.setdefault("repo_count", 0)
        return cache
    except (OSError, json.JSONDecodeError):
        print("  cache unreadable; rebuilding everything")
        return {"version": 1, "repo_count": 0, "repos": {}}


### Main Program ###


def build(output_root, image_root, token, dry_run):
    """Run the full build.

    Args:
        output_root: Directory to write the finished site into.
        image_root: Directory downloaded preview images are written to. The same as
            output_root for a real build, and a scratch directory for a dry run so that
            nothing already on disk changes.
        token: GitHub token, or None for unauthenticated requests.
        dry_run: True to fetch and render everything but write nothing.

    Returns:
        int: Process exit code, 0 on success.
    """
    templates = ROOT / "templates"
    index_template = (templates / "index.html").read_text(encoding="utf-8")
    detail_template = (templates / "repo.html").read_text(encoding="utf-8")

    cache = load_cache(output_root)

    print(f"Fetching repositories for {ORG} ({'authenticated' if token else 'anonymous'})...")
    api_repos = fetch_org_repositories(token)
    visible = [
        repo
        for repo in api_repos
        if not repo.get("private") and repo.get("name") not in IGNORED_REPOS
    ]
    records = sorted((to_record(repo) for repo in visible), key=lambda r: r["name"].lower())

    ### Validate Inputs ###

    if not records:
        raise BuildError("The API returned no publishable repositories; keeping the last build.")

    previous_count = cache.get("repo_count", 0)
    if previous_count and len(records) < previous_count * MIN_REPO_RATIO:
        raise BuildError(
            f"Repository count fell from {previous_count} to {len(records)}, which looks like a "
            "partial API response. Keeping the last build; rerun to confirm."
        )

    if any(record["slug"].lower() == DETAIL_PATH_PREFIX for record in records):
        raise BuildError(
            f"A repository named {DETAIL_PATH_PREFIX!r} exists. Its GitHub Pages site would "
            f"shadow every page under /{DETAIL_PATH_PREFIX}/. Change DETAIL_PATH_PREFIX."
        )

    ### Retrieve Source Data ###

    placeholder_shas = set()
    template_tree = fetch_tree(TEMPLATE_REPO, "HEAD", token)
    for path in TEMPLATE_PLACEHOLDER_PATHS:
        entry = template_tree.get(path)
        if entry and entry.get("sha"):
            placeholder_shas.add(entry["sha"])
    if not placeholder_shas:
        print(f"  warning: could not read placeholders from {TEMPLATE_REPO}; guard is inactive")

    def gather(record):
        """Fetch one repository's README and file list, and resolve its preview images."""
        slug = record["slug"]
        entry = dict(cache["repos"].get(slug, {}))
        fragment_path = output_root / README_FRAGMENT_DIR / f"{slug}.html"

        # A cached ETag is only usable while the fragment it produced is still on disk.
        etag = entry.get("readme_etag") if fragment_path.exists() else None
        rendered, new_etag = fetch_readme_html(slug, token, etag)
        if rendered is None and etag and new_etag:
            readme_html = extract_cached_readme(fragment_path)
        else:
            readme_html = (
                process_readme(rendered, slug, record["default_branch"]) if rendered else ""
            )
        entry["readme_etag"] = new_etag or ""

        tree = fetch_tree(slug, record["default_branch"], token)
        resolve_images(record, tree, placeholder_shas, token, image_root, entry)
        return slug, readme_html, entry

    readmes = {}
    workers = MAX_WORKERS if token else MAX_WORKERS_ANONYMOUS
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for slug, readme_html, entry in pool.map(gather, records):
            readmes[slug] = readme_html
            cache["repos"][slug] = entry

    ### Save Results ###

    pages = {"index.html": mark_generated(render_index(index_template, records))}
    for record in records:
        slug = record["slug"]
        pages[f"{DETAIL_PATH_PREFIX}/{slug}/index.html"] = mark_generated(
            render_detail_page(detail_template, record, readmes[slug])
        )
        pages[f"{README_FRAGMENT_DIR}/{slug}.html"] = render_panel_fragment(
            record, readmes[slug]
        )
    pages["sitemap.xml"] = render_sitemap(records)
    pages[LLMS_TXT_PATH] = render_llms_txt(records)
    pages[CATALOG_PATH] = json.dumps(records, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    cache["repo_count"] = len(records)
    pages[CACHE_PATH] = json.dumps(cache, indent=2, sort_keys=True) + "\n"

    for record in records:
        readme_state = "readme" if readmes[record["slug"]] else "no readme"
        featured = "featured" if record["featured"] else ""
        print(
            f"  {record['slug']:<46} {record['image_source']:<11} {readme_state:<9} {featured}"
        )

    if dry_run:
        print(f"\nDry run: {len(pages)} files would be written to {output_root}. Nothing changed.")
        return 0

    for relative, text in pages.items():
        write_text(output_root / relative, text)
    prune_stale(output_root, {record["slug"] for record in records})

    print(f"\nWrote {len(pages)} files for {len(records)} repositories to {output_root}.")
    return 0


READ_FRAGMENT_README_RE = re.compile(r'<div class="panel-readme">(.*)</div>\s*$', re.S)


def extract_cached_readme(fragment_path):
    """Recover the sanitized README from a panel fragment written by an earlier build.

    Reusing it avoids re-rendering content GitHub reported as unchanged.

    Args:
        fragment_path: Path to data/readme/<slug>.html.

    Returns:
        str: The README markup, or an empty string when the fragment cannot be parsed.
    """
    try:
        text = fragment_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # The README block is followed only by the closing links row, so trim that first.
    text = re.sub(r'\n<div class="repo-links panel-links-bottom">.*$', "", text, flags=re.S)
    match = READ_FRAGMENT_README_RE.search(text)
    return match.group(1).strip() if match else ""


def main(argv=None):
    """Parse arguments and run the build.

    Args:
        argv: Command-line arguments, or None to read from sys.argv.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description="Build the Open Source Hub as static files.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT),
        help="Directory to write the site into. Defaults to the repository root.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Fetch and render everything and report the result, but write nothing. Preview "
            "images are re-downloaded on every dry run because the on-disk cache is bypassed."
        ),
    )
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None
    output_root = Path(args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        if args.dry_run:
            # Images are still downloaded so the report is accurate, but they go to a scratch
            # directory that disappears when the run ends.
            with tempfile.TemporaryDirectory(prefix="efdc-site-dryrun-") as scratch:
                return build(output_root, Path(scratch), token, True)
        return build(output_root, output_root, token, False)
    except BuildError as error:
        print(f"\nBuild failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
