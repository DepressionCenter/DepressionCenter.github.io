<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## Compliance

[Back to the project README](../README.md)

This page records the security and accessibility measures actually in place on the Open Source
Hub, what has been tested, and what still needs a person to check. It states evidence, not
intentions. Anything not yet verified is listed as outstanding rather than assumed to pass.

**Last reviewed:** 2026-09-01, covering the change from a browser-built page to a
pre-built static site.

## Data handled

None that is sensitive. Every input is already public on GitHub: repository names,
descriptions, topics, licences, READMEs, and image files. The site has no login, no form, no
database, and nothing a visitor submits. **No Protected Health Information and no participant
data pass through any part of this system.** See [data flow](data-flow.md) for the detail.

## Security measures in place

| Risk | Measure | Where |
| --- | --- | --- |
| Markup injected through a repository description, name, or custom property | Every value is escaped with `html.escape(..., quote=True)` before it reaches a page | `esc()` in `scripts/build_site.py` |
| Script injected through a README | Allowlist sanitizer (`nh3`) over GitHub's already-rendered HTML; unknown tags and all event handlers are removed | `process_readme()` |
| `javascript:` or `data:` links from a repository homepage or custom property | Only `http` and `https` schemes are accepted; anything else becomes an empty string and the link is not rendered | `safe_url()` |
| Unsafe schemes inside a README link | Sanitizer restricts link schemes to `http`, `https`, and `mailto` | `README_URL_SCHEMES` |
| A crafted file path redirecting a build request elsewhere | Requests are refused unless the host is `api.github.com` or `raw.githubusercontent.com` | `_check_host()` |
| A malicious or malformed image consuming the runner | Files over 8 MB are skipped and Pillow's decoded-pixel ceiling is set to 80 megapixels | `MAX_REMOTE_IMAGE_BYTES`, `imagelib.py` |
| A failed or partial API response wiping the published site | The build stops without writing when the repository list is empty or has shrunk by more than 30 percent | `build()` |
| Credentials in the repository | None exist. The build runs unauthenticated; in Actions it uses the automatically issued `GITHUB_TOKEN`, which is created per run and never stored | `.github/workflows/build-site.yml` |

The workflow requests `contents: write` and nothing else, and it is guarded so it cannot run in
a fork.

### The sanitizer allowlist

`nh3` is configured with an explicit list of tags and per-tag attributes in
`scripts/build_site.py` (`README_TAGS`, `README_ATTRIBUTES`). Two decisions are worth
recording:

- **SVG is not allowed.** The only SVG GitHub emits in a README is the decorative icon inside a
  note or warning callout. Dropping it removes a whole class of risk and costs only the icon;
  the callout keeps its coloured bar and its title.
- **`rel` is not in the allowed attribute list for links.** The sanitizer sets
  `rel="nofollow noopener noreferrer"` on every link itself, and it refuses to do both.

The sanitizer is a maintained library. Sanitizing is never hand-rolled here.

### Dependencies

Two, both pinned in `requirements.txt`: `Pillow==12.3.0` and `nh3==0.3.7`. Both were the
current releases as of 2026-09-01, and `nh3` is the documented successor to `bleach`. No
Node.js, no bundler, and no framework. Raise the pins deliberately rather than automatically.

### Security testing performed

`python scripts/test_build_site.py` runs 34 offline checks. Result on 2026-09-01:
**34/34 passed.** They cover a hostile description, a hostile lab name, `javascript:` and
`data:` URLs in every author-controlled field, a README containing a script tag, an iframe, an
`onerror` handler and a `javascript:` link, and a request aimed at a host outside the
allowlist. The suite also checks that a cached rebuild reproduces the previous output exactly,
so a nightly run cannot quietly degrade a page it did not re-fetch.

Also confirmed by inspecting the generated output: none of the 26 rendered README blocks
contains a `<script>`, `<svg>`, event handler, or `javascript:` URL.

## Accessibility

**Target: WCAG 2.1 AA.** The visual design, colour palette, and layout are unchanged from the
previous version of the site; this record covers the structural changes made when the site
became static.

### Improvements made in this change

| Change | Why it matters |
| --- | --- |
| Card titles are real links (`<a href>`) instead of `<button>` elements | The page works with scripting unavailable, and Ctrl-click, middle-click, and "open in new tab" behave normally |
| Each card has one tab stop instead of three | The preview image and the description are still clickable with a mouse but are no longer separate keyboard stops repeating the same destination |
| Preview images are marked decorative (`alt=""`, `aria-hidden`) | The repository name sits beside the image as real text, so announcing the image would only repeat it |
| Tags are `<button>` elements instead of `<span role="button">` | Native keyboard behaviour rather than a hand-built imitation |
| Tags on repository pages are plain text, not buttons | There is no grid to filter there, so a control that did nothing would mislead |
| README headings shift down one level | Every page has exactly one `<h1>`, which is the repository name |
| Repository pages carry a skip link, `<main>`, and `lang="en"` | Same landmarks as the landing page |
| `<!DOCTYPE html>` added | The previous `index.html` had none |
| The `aria-live` region no longer wraps the repository grid | With content in the HTML, a live region would announce all 26 cards on load. The count label keeps `aria-live` |
| Animated GIF previews are flattened to a single frame | Nothing on a card moves on its own |
| The panel keeps its focus trap, Escape handling, and focus return | Behaviour preserved from the previous version |
| The panel now closes with the browser Back button | The panel has a real URL, so the expected control works |

The existing `prefers-reduced-motion` and `prefers-contrast: high` rules are carried over
unchanged in `styles/site.css`.

### Accessibility testing performed

Verified on 2026-09-01 by inspecting the generated markup and serving the site locally:

- Every repository page has exactly one `<h1>`.
- All 26 cards, with their descriptions, tags, and links, are present in `index.html` as
  delivered, with no scripting involved.
- Every generated page returns HTTP 200 along with its stylesheet, script, images, and sitemap.

### Outstanding: needs a person

These require a human at a browser and have **not** been done:

- [ ] Keyboard-only pass over the landing page and the panel: tab order, the focus trap, focus
      return on close, and a visible focus indicator throughout.
- [ ] Screen reader pass on opening and closing the panel, and on one repository page.
- [ ] Zoom to 200% and reflow at 320 CSS pixels with no horizontal scrolling, including the
      wide Community Open Source table and any wide tables inside a README.
- [ ] axe or Lighthouse run against the landing page and one repository page.
- [ ] Contrast check on the new repository-page styles (breadcrumb, title, back link) at 4.5:1
      for normal text and 3:1 for large text and UI components.
- [ ] Confirm that README tables and code blocks scroll inside their own container rather than
      forcing the page sideways.

Until those are done, this page claims structural conformance work only, not verified WCAG 2.1
AA conformance.

## Known gaps

- **README images are hot-linked.** They load from `camo.githubusercontent.com`, exactly as on
  GitHub. That leaves a third-party dependency in the rendered page. Mirroring them locally is
  possible but was not part of this change.
- **Content can be up to a day old.** The build runs nightly. A correction made in the morning
  appears the next night unless someone runs the workflow by hand.
- **Analytics.** Google Analytics loads on `depressioncenter.org` and `umich.edu` domains only.
  This behaviour is unchanged and was not reviewed as part of this work.
- **A second consecutive build has not been observed end to end.** The build was run
  successfully and its output verified, but the anonymous rate limit prevented running it
  twice in a row to watch the ETag and image-hash cache skip unchanged work. The cache's
  recovery step is covered by the offline checks above; the live path is not.

## Conclusion

The security posture rests on escaping everything, sanitizing README markup with a maintained
library, restricting link schemes and network hosts, and refusing to publish a suspicious
build. The accessibility posture improved structurally, but the manual checks listed above are
still owed before anyone claims conformance.

## Additional resources

+ [Data flow](data-flow.md)
+ [Architecture](architecture.md)
+ [WCAG 2.1 at the W3C](https://www.w3.org/TR/WCAG21/)
+ [OWASP Top 10](https://owasp.org/www-project-top-ten/)
+ [nh3 documentation](https://nh3.readthedocs.io/)

[Back to the project README](../README.md)
