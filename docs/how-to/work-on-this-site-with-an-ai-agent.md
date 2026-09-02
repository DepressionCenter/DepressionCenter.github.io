<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## How to Work on This Site with an AI Agent

[Back to the project README](../../README.md)

A starting prompt to paste into a new AI coding session, and the reasoning behind it. The
prompt tells an agent the handful of things about this repository that are not obvious from
reading the code, and that it would otherwise get wrong. Copy the block below, add what you
want changed at the end, and send it.

## The prompt

```text
You are working on the Eisenberg Family Depression Center Open Source Hub, the static
site published at https://code.depressioncenter.org from this repository.

READ FIRST, BEFORE ANY CHANGE
- AGENTS.md in the repository root. It is binding: file headers, comment style,
  security rules, accessibility rules, and the response format all come from it.
- docs/architecture.md for how the site is put together.

HOW THE SITE WORKS
A Python script reads the organization's public repositories from the GitHub API once a
night and writes finished HTML into this repository. GitHub Pages serves those files.
Nothing is assembled in the visitor's browser. The point of this design is that search
engines and visitors without JavaScript get the full content, so do not undo it.

NEVER EDIT THESE. THEY ARE GENERATED AND WILL BE OVERWRITTEN:
  index.html, repos/**, data/readme/**, data/repos.json, data/build-cache.json,
  sitemap.xml, llms.txt, images/repo-previews/remote/**
EDIT THESE INSTEAD:
  templates/index.html      page shell for the landing page
  templates/repo.html       page shell for one repository page
  styles/site.css           all styling, shared by every page
  scripts/site.js           search, tag filtering, the slide-in panel
  scripts/build_site.py     the build itself
  scripts/resources.py      the Center's resource list shown on the page and in llms.txt
Then run the build to regenerate the output.

COMMANDS
  pip install -r requirements.txt      once; installs Pillow and nh3, nothing else
  python scripts/test_build_site.py    52 offline checks, no network, run this often
  python scripts/build_site.py         writes the site into the repository root
  python scripts/build_site.py --dry-run   fetch and report, write nothing
  python -m http.server 8000           then open http://localhost:8000

THINGS THAT WILL BITE YOU IF NOBODY TELLS YOU
1. Rate limit. Unauthenticated GitHub allows 60 requests an hour and one build uses
   about 55, so a second build in the same hour fails. It fails safely and writes
   nothing. Set GH_TOKEN to any token with no scopes to get 5,000 an hour. Do not
   assume a failed build means broken code; check the message first.
2. Third-party GitHub Actions are blocked. The University of Michigan enterprise allows
   only actions published by GitHub itself (actions/*, github/*) and actions owned by
   the organization. Anything from the wider marketplace is refused and the job never
   runs. .github/workflows/build-site.yml currently uses no actions at all, which is
   always safe; if you add one, it must be a GitHub-published or organization-owned
   action, and say which in your summary so it can be checked.
3. Repository pages live at /repos/<name>/, never at /<name>/. Other repositories in
   the organization publish their own GitHub Pages sites at the root path, and would
   shadow anything written there.
4. Size every inline SVG in the markup with width and height attributes, not only in
   CSS. An SVG with only a viewBox has no intrinsic size and fills its container
   whenever the stylesheet is stale, missing, or still loading.
5. GitHub only rewrites Markdown image syntax when it renders a README. Raw HTML tags
   keep their relative paths, so the build resolves them itself.

NON-NEGOTIABLE
- Everything from the GitHub API is untrusted input. Escape every value that reaches a
  page, and sanitize README markup through the existing nh3 allowlist. Never disable it.
- Accessibility is an acceptance criterion, not a nice-to-have. In particular: never
  hide content behind hover, keep one h1 per page, keep contrast at 4.5:1 for text and
  3:1 for icons, and keep the site working with JavaScript turned off.
- Do not commit or push unless I ask.

BEFORE YOU TELL ME YOU ARE DONE
- Run scripts/test_build_site.py and report the real result.
- Run the build and show me `git status` so I can see exactly what changed.
- Load the page with JavaScript disabled and confirm the repository list and links
  still work. That is the acceptance test for this site.
- Say plainly what you verified by running it and what you only reasoned about.

WHAT I WANT CHANGED
<describe your change here>
```

## Why each part is there

The prompt is short because most of the rules already live in `AGENTS.md`, which any competent
agent will read when told to. What it adds are the five things an agent cannot infer from the
code, each of which was learned the hard way while the site was being built:

| Item | What goes wrong without it |
| --- | --- |
| Generated versus source files | An agent edits `index.html`, the change looks right, and the next build silently erases it. |
| The rate limit | A failed build looks like broken code. It is not; it is the hourly quota, and the build refuses to publish rather than write a partial site. |
| Third-party actions are blocked | A workflow that reaches for a marketplace action is refused by enterprise policy and the job never runs. Only GitHub-published and organization-owned actions are permitted. |
| Detail pages under `/repos/` | Pages written to `/<name>/` are shadowed by that repository's own site and are never served. |
| Sizing SVGs in markup | An icon with only a `viewBox` expands to fill the page whenever the stylesheet has not arrived. |

The closing instruction, to separate what was verified by running from what was only reasoned
about, matters more than it looks. Much of this site can be regenerated offline from files
already on disk, which produces the right answer but is not the same as having run the build.
Asking for that distinction keeps the difference visible.

## Conclusion

Paste the prompt, describe your change at the end, and check the two things it asks the agent
to show you: the test result and `git status`. If a build fails, read the message before
assuming the code is wrong.

## Additional resources

+ [Architecture](../architecture.md)
+ [How to run the build locally](run-the-build-locally.md)
+ [Troubleshooting](../troubleshooting.md)
+ [Compliance](../compliance.md)
+ [AGENTS.md](../../AGENTS.md)

[Back to the project README](../../README.md)
