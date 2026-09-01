<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## Troubleshooting

[Back to the project README](../README.md)

Known ways the site build fails, what causes each one, and what to do about it. Every failure
listed here stops the build **before** it writes anything, so the site stays as it was.

## The build stops with a rate limit message

**Symptom.** `GitHub API rate limit exhausted; resets at ...`

**Cause.** Without a token, GitHub allows 60 requests an hour from one address, and a full
build uses about 55. A second build in the same hour runs out.

**Fix.** Wait for the reset time in the message, or set a token as described in
[how to run the build locally](how-to/run-the-build-locally.md). Inside GitHub Actions this
should not happen: the workflow passes `GITHUB_TOKEN`, which allows 1,000 requests an hour.

## The build stops saying the repository count fell

**Symptom.** `Repository count fell from 26 to 9, which looks like a partial API response.`

**Cause.** The build refuses to publish when the repository list shrinks by more than 30
percent, because that usually means a partial or failed API response rather than nine
repositories actually being deleted.

**Fix.** Run it again. If the smaller number is genuinely correct, run it a second time; the
count is compared against `data/build-cache.json`, so once a smaller count is recorded the
check settles. If the count is wrong, look at whether repositories were made private by
mistake.

## The build stops over a repository named "repos"

**Symptom.** `A repository named 'repos' exists. Its GitHub Pages site would shadow every page
under /repos/.`

**Cause.** GitHub Pages decides which site serves a URL by matching the first part of the path
against a repository name. A repository called `repos` would take over every repository detail
page on this site.

**Fix.** Rename that repository, or change `DETAIL_PATH_PREFIX` in `scripts/build_site.py` to
something no repository is named, and rebuild. Remember that changing it moves every page to a
new URL, so add redirects or accept the loss of the old links.

## A repository shows the wrong picture

**Symptom.** A card shows the generic template placeholder, or the initials, or an image you
did not expect.

**Cause.** The build picks images in a fixed order and stops at the first one it finds.

**Fix.** Open `data/repos.json`, find the repository, and read `image_source`. See
[how to add a repository preview image](how-to/add-a-repo-preview-image.md) for what each
value means and how to change the outcome. Two common cases:

- `placeholder` when you expected an image: the file name or its capitalization does not match
  what the build looks for.
- `local` when the repository does have a `Repo-preview.png`: that file is byte-for-byte the
  untouched template placeholder, which the build deliberately ignores. Replace it with a real
  screenshot.

## A README looks different from how it looks on GitHub

**Symptom.** Note and warning callouts have no icon, or something else is missing.

**Cause.** The build strips SVG from README markup, and GitHub's callout icons are SVG. The
callout keeps its coloured bar and its title, so the meaning survives; only the icon is gone.
Anything else missing was removed by the sanitizer, which allows a fixed list of tags.

**Fix.** If a README genuinely needs a tag that is being dropped, add it to `README_TAGS` in
`scripts/build_site.py` and note the change in [compliance](compliance.md). Do not disable
sanitizing.

## A repository page returns "not found"

**Symptom.** `code.depressioncenter.org/repos/SomeRepo/` gives a 404.

**Cause.** Either the build has not run since that repository appeared, or the repository is
private, archived out of view, or on the ignore list in `scripts/build_site.py`.

**Fix.** Check that it appears in `data/repos.json`. If not, confirm it is public and not in
`IGNORED_REPOS`, then run the workflow by hand from the Actions tab.

## The nightly build stopped running

**Symptom.** No new commits from the workflow for weeks.

**Cause.** GitHub disables scheduled workflows in a repository with no activity for 60 days.

**Fix.** Open the Actions tab and run **Build site** manually; that re-enables the schedule.
Any push to `main` also counts as activity.

## Conclusion

Most failures here are the build protecting the published site rather than something being
broken. Read the message, check `data/repos.json`, and rerun.

## Additional resources

+ [How to run the build locally](how-to/run-the-build-locally.md)
+ [How to add a repository preview image](how-to/add-a-repo-preview-image.md)
+ [Architecture](architecture.md)
+ [GitHub API rate limits](https://docs.github.com/rest/using-the-rest-api/rate-limits-for-the-rest-api)

[Back to the project README](../README.md)
