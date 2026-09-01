#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# test_build_site.py - Checks for the site build, covering escaping, sanitizing, and edge cases.
# Author(s): Gabriel Mongefranco.
# Created: 2026-09-01
# Last Modified: 2026-09-01
# Summary: Verify that content coming from the GitHub API cannot inject markup into a page,
#          that unsafe link schemes are dropped, and that the build's boundary cases behave.
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
"""Offline checks for scripts/build_site.py.

Run with `python scripts/test_build_site.py`. Nothing here touches the network, so it is safe
to run repeatedly and does not consume the GitHub API rate limit.

A repository description, homepage, and custom properties are all set by whoever owns that
repository, and a README is fetched at build time. All of it is untrusted input, so most of
these checks are negative: they confirm hostile content is rendered harmless rather than
executed.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_site as build

# A repository record whose every author-controlled field carries an attack.
HOSTILE_API_REPO = {
    "name": "Evil-Repo",
    "description": '<script>alert(1)</script> and "quotes" & <img src=x onerror=alert(2)>',
    "html_url": "https://github.com/DepressionCenter/Evil-Repo",
    "homepage": "javascript:alert('xss')",
    "custom_properties": {
        "featured": "true",
        "demo_url": "data:text/html,<script>alert(3)</script>",
        "docs_url": "https://example.org/docs",
        "lab_name": "</span><script>alert(4)</script>",
        "lab_url": "javascript:void(0)",
    },
    "language": "HTML",
    "topics": ["a"],
    "pushed_at": "2026-01-01T00:00:00Z",
    "default_branch": "main",
}

HOSTILE_README = (
    '<div id="readme" class="md" data-path="README.md"><article class="markdown-body">'
    "<h1>Title</h1><script>alert(1)</script>"
    '<p><img src=x onerror="alert(2)"><a href="javascript:alert(3)">bad</a>'
    '<a href="https://example.org">good</a><a href="#section">anchor</a></p>'
    '<iframe src="https://evil.example"></iframe>'
    '<p><img src="./images/shot.png"><img src="/images/root.png">'
    '<a href="docs/guide.md">guide</a><a href="src/">folder</a>'
    '<a href="../outside.md">outside</a></p>'
    "<h2>Sub</h2></article></div>"
)

results = []


def check(description, condition, detail=""):
    """Record one check and print its outcome.

    Args:
        description: What the check proves, in plain language.
        condition: Truthy when the check passed.
        detail: Extra context printed when the check fails.
    """
    results.append(bool(condition))
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {description}")
    if not condition and detail:
        print(f"         {detail}")


def test_hostile_repository_fields():
    """A hostile description or URL must never become live markup or a live link."""
    print("Repository fields from the API")
    record = build.to_record(HOSTILE_API_REPO)
    card = build.render_card(record, featured=False)

    check("script tag in a description does not become a tag", "<script>" not in card)
    check("img tag in a description does not become a tag", "<img src=x" not in card)
    check(
        "the description is still visible as text",
        "&lt;script&gt;" in card and "&lt;img src=x" in card,
    )

    attribute_values = re.findall(r'="([^"]*)"', card)
    leaked = [value for value in attribute_values if "<" in value or ">" in value]
    check("no raw markup escapes into an attribute", not leaked, f"leaked: {leaked[:2]}")

    check("a javascript: homepage is dropped", record["website"] == "")
    check("a data: demo URL is dropped", record["demo"] == "")
    check("a javascript: lab URL is dropped", record["lab_url"] == "")
    check("a valid https URL is kept", record["docs"] == "https://example.org/docs")

    lab = build.render_lab(record)
    check("a hostile lab name is escaped", "<script>" not in lab and "&lt;script&gt;" in lab)


def test_readme_sanitizing():
    """README markup arrives from the API and must be reduced to a safe subset."""
    print("README markup from the API")
    markup = build.process_readme(HOSTILE_README, "Evil-Repo", "main")

    for pattern in ("<script", "onerror", "javascript:", "<iframe"):
        check(f"{pattern} is removed", pattern not in markup.lower())

    check(
        "headings shift down so the page keeps a single h1",
        "<h2>Title</h2>" in markup and "<h3>Sub</h3>" in markup,
        markup,
    )

    external = re.search(r'<a[^>]*href="https://example\.org"[^>]*>', markup)
    anchor = re.search(r'<a[^>]*href="#section"[^>]*>', markup)
    check("an external link opens in a new tab", external and 'target="_blank"' in external.group(0))
    check(
        "an external link carries rel protections",
        external and 'rel="nofollow noopener noreferrer"' in external.group(0),
    )
    check(
        "an in-page anchor does not open a new tab",
        anchor and 'target="_blank"' not in anchor.group(0),
    )
    check(
        "empty input is handled",
        build.process_readme("", "Evil-Repo", "main") == ""
        and build.process_readme(None, "Evil-Repo", "main") == "",
    )


def test_relative_readme_links():
    """GitHub leaves raw HTML tags in a README alone, so relative paths must be resolved here.

    A README written with <img src="images/shot.png"> points at nothing once its markup is
    shown on this site, because the page it lands on is not in that repository.
    """
    print("Relative links inside a README")
    markup = build.process_readme(HOSTILE_README, "Evil-Repo", "main")
    raw = "https://raw.githubusercontent.com/DepressionCenter/Evil-Repo/main/"
    repo = "https://github.com/DepressionCenter/Evil-Repo"

    check('a "./" image path resolves to the raw file host', f'src="{raw}images/shot.png"' in markup, markup)
    check('a "/" image path is treated as repository-root', f'src="{raw}images/root.png"' in markup)
    check("a link to a file goes to the blob view", f'href="{repo}/blob/main/docs/guide.md"' in markup)
    check("a link to a folder goes to the tree view", f'href="{repo}/tree/main/src/"' in markup)
    check('a path climbing above the repository is left alone', 'href="../outside.md"' in markup)
    check("an in-page anchor is left alone", 'href="#section"' in markup)
    check(
        "a newly absolute link still opens in a new tab",
        'target="_blank"' in (re.search(r'<a[^>]*docs/guide\.md"[^>]*>', markup) or type("x", (), {"group": lambda s, n=0: ""})()).group(0),
    )


def test_network_allowlist():
    """Image paths come from the API, so the build only ever contacts two known hosts."""
    print("Network allowlist")
    try:
        build._check_host("https://evil.example/steal")
        check("a request to another host is refused", False)
    except build.BuildError:
        check("a request to another host is refused", True)
    try:
        build._check_host("https://api.github.com/orgs/x/repos")
        check("a request to the GitHub API is allowed", True)
    except build.BuildError:
        check("a request to the GitHub API is allowed", False)


def test_boundaries():
    """Empty, oversized, and awkward values must not crash or produce broken output."""
    print("Boundary cases")
    check("initials come from the first two words", build.monogram("MTC-SharePoint-Site") == "MS")
    check("an empty name yields no initials", build.monogram("") == "")
    check("missing language and topics yield no tags", build.build_tags(None, None) == [])
    check(
        "organization topics and duplicates are dropped",
        build.build_tags("Python", ["umich", "python", "EFDC", "r"]) == ["Python", "r"],
    )
    check(
        "tags are capped",
        len(build.build_tags("Python", [f"t{i}" for i in range(20)])) == build.MAX_TAGS,
    )
    check("an empty description yields an empty summary", build.meta_description("") == "")

    trimmed = build.meta_description("word " * 100)
    check(
        "a long description is trimmed and marked",
        len(trimmed) <= build.META_DESCRIPTION_LIMIT + 1 and trimmed.endswith("…"),
    )
    check("repository names are percent-encoded in URLs", build.detail_url("A B") == "repos/A%20B/")
    check(
        "a repository with no preview falls back to initials",
        "thumb-monogram" in build.render_thumb(build.to_record(HOSTILE_API_REPO), "", "x"),
    )


def test_template_safety():
    """A template token left unfilled would publish a visibly broken page."""
    print("Templates")
    try:
        build.fill("<p>{{MISSING}}</p>", {})
        check("an unfilled token stops the build", False)
    except build.BuildError:
        check("an unfilled token stops the build", True)
    check("a filled token is substituted", build.fill("<p>{{A}}</p>", {"A": "x"}) == "<p>x</p>")


def test_cache_round_trip():
    """A cached rebuild must reproduce the previous output exactly.

    When GitHub reports a README as unchanged, the build recovers it from the fragment written
    last time instead of re-rendering. If that recovery lost anything, a nightly rebuild would
    quietly degrade every page, and the damage would be easy to miss.

    Skipped when the site has not been built yet, because it reads the generated files.
    """
    print("Cache round-trip against generated output")
    root = Path(__file__).resolve().parent.parent
    catalog = root / "data" / "repos.json"
    if not catalog.exists():
        print("  [skip] no generated output; run scripts/build_site.py first")
        return

    records = json.loads(catalog.read_text(encoding="utf-8"))
    index_template = (root / "templates" / "index.html").read_text(encoding="utf-8")
    repo_template = (root / "templates" / "repo.html").read_text(encoding="utf-8")

    check(
        "rendering the landing page twice gives identical bytes",
        build.render_index(index_template, records) == build.render_index(index_template, records),
    )

    unstable = []
    unrepeatable = []
    for record in records:
        fragment = root / "data" / "readme" / f"{record['slug']}.html"
        if not fragment.exists():
            continue
        recovered = build.extract_cached_readme(fragment)
        if build.render_panel_fragment(record, recovered) != fragment.read_text(encoding="utf-8"):
            unstable.append(record["slug"])
        first = build.render_detail_page(repo_template, record, recovered)
        if first != build.render_detail_page(repo_template, record, recovered):
            unrepeatable.append(record["slug"])

    check(
        f"every panel fragment rebuilds identically from cache ({len(records)} repositories)",
        not unstable,
        f"unstable: {unstable[:5]}",
    )
    check(
        "rendering a repository page twice gives identical bytes",
        not unrepeatable,
        f"unrepeatable: {unrepeatable[:5]}",
    )


def main():
    """Run every check and report the total.

    Returns:
        int: 0 when every check passed, 1 otherwise.
    """
    for test in (
        test_hostile_repository_fields,
        test_readme_sanitizing,
        test_network_allowlist,
        test_boundaries,
        test_relative_readme_links,
        test_template_safety,
        test_cache_round_trip,
    ):
        test()
        print()

    failures = results.count(False)
    print(f"{len(results) - failures}/{len(results)} checks passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
