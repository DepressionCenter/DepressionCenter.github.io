<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## Data Flow

[Back to the project README](../README.md)

This page traces every piece of content on the site back to where it came from. It covers what
the build reads, how it changes that content, and where the result is stored. It is written
for a maintainer or an auditor who needs to know exactly what this site publishes.

**No participant data is involved anywhere in this pipeline.** Everything the build reads is
already public on GitHub: repository names, descriptions, topics, READMEs, and image files.
There is no database, no login, no form, and nothing a visitor submits.

## What the build reads

All four requests go to GitHub. Nothing else is contacted.

| Source | Endpoint | What it provides |
| --- | --- | --- |
| Repository list | `GET /orgs/DepressionCenter/repos` | Name, description, homepage, language, topics, licence, last push date, and the organization's custom properties. |
| README | `GET /repos/{org}/{repo}/readme` with `Accept: application/vnd.github.html+json` | The README already rendered to HTML by GitHub. |
| File list | `GET /repos/{org}/{repo}/git/trees/{branch}?recursive=1` | Every file path, its size, and its content hash. Used to find preview images. |
| Preview image | `raw.githubusercontent.com/...` | The image file itself, downloaded only when one was found. |

Custom properties are set per repository in the organization's settings. The build reads five:

| Property | Meaning | Type |
| --- | --- | --- |
| `featured` | Show this repository in the Featured section. | Text; compared against `"true"` |
| `lab_name` | Name of the lab or team that owns the work. | Text |
| `lab_url` | Link for that lab or team. | URL |
| `demo_url` | Link to a live demonstration. | URL |
| `docs_url` | Link to documentation. | URL |

Dates come from GitHub as ISO 8601 timestamps in UTC (`2026-08-14T17:22:01Z`) and are stored
and published exactly as received. They are never converted to a local time zone.

## How the content is transformed

1. **Filter.** Private repositories are dropped, as are `.github`, `.github-private`, and this
   repository itself.
2. **Validate.** The build stops without writing anything if the list is empty, if the count
   fell by more than 30 percent since the last build, or if a repository named `repos` exists.
3. **Escape.** Every value that comes from GitHub is HTML-escaped before it reaches a page. A
   repository description containing markup renders as visible text, never as markup.
4. **Sanitize.** README HTML passes through an allowlist sanitizer. Only known-safe tags and
   attributes survive, and links may only use `http`, `https`, or `mailto`.
5. **Resolve relative links.** GitHub rewrites Markdown image syntax to absolute proxy URLs
   when it renders a README, but it leaves raw HTML tags alone. A README containing
   `<img src="images/shot.png">` therefore arrives with a path that means nothing on this
   site, so the build points it at `raw.githubusercontent.com`. Relative links become GitHub
   `blob` or `tree` URLs depending on whether the target looks like a file or a folder.
6. **Restructure.** Headings in the README shift down one level so each page has exactly one
   `<h1>`, which is the repository name. The Center's logo is removed from the top of each
   README because the site header already shows it.
7. **Normalize images.** Preview images are centre-cropped to 16:9 and resized to 912 pixels
   wide, with a 360-pixel thumbnail. Animated images keep only their first frame.

## Where the results land

| Output | Contents |
| --- | --- |
| `index.html` | The landing page, with every repository card written into the HTML. |
| `repos/<name>/index.html` | One page per repository, holding the full README. |
| `data/readme/<name>.html` | The same content as a fragment, loaded by the slide-in panel. |
| `data/repos.json` | The catalog as machine-readable JSON, including which image each card uses. |
| `data/build-cache.json` | ETags and image hashes, so unchanged content is not downloaded again. |
| `images/repo-previews/remote/` | Preview images pulled from other repositories. |
| `sitemap.xml` | Every page on the site, with real modification dates. |
| `llms.html` | A human-readable site index containing every Center resource and repository. |
| `llms.txt` | A plain-text map of the collection for language models and agents, listing the Center's public resources and every repository with its source, documentation, and demo links. |

All of it is committed to the `main` branch and served by GitHub Pages. There is no separate
deployment step and no build artifact stored outside the repository.

## What is deliberately not stored

- **README images are not copied here.** They stay on GitHub's image proxy
  (`camo.githubusercontent.com`), exactly as they appear on GitHub itself. This keeps the
  build small, at the cost of one third-party dependency in the rendered page.
- **No analytics data is written by the build.** The page loads Google Analytics only on
  `depressioncenter.org` and `umich.edu` domains, which is unchanged from before.

## Conclusion

Everything on this site is public GitHub content, escaped and sanitized on the way in, and
written to plain files. If you need to know why a particular card looks the way it does, open
`data/repos.json` and read the `image_source` field for that repository.

## Additional resources

+ [Architecture](architecture.md)
+ [How to add a repository preview image](how-to/add-a-repo-preview-image.md)
+ [Compliance](compliance.md)
+ [GitHub custom properties documentation](https://docs.github.com/organizations/managing-organization-settings/managing-custom-properties-for-repositories-in-your-organization)

[Back to the project README](../README.md)
