<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## How to Run the Build Locally

[Back to the project README](../../README.md)

Run the build on your own computer to preview a change before it goes live. You need Python
3.9 or newer and about a minute. You do not need a GitHub account, a token, or any credentials.

## Set up, once

```
python -m venv .venv
.venv/Scripts/activate        # On macOS or Linux: source .venv/bin/activate
pip install -r requirements.txt
```

That installs two packages: `Pillow` to resize images and `nh3` to sanitize README markup.

## Preview without changing anything

```
python scripts/build_site.py --dry-run
```

This fetches everything and prints one line per repository showing which image it chose and
whether it found a README, but writes nothing to disk. Use it to check your work before a real
build.

Note that a dry run downloads every preview image again, because it deliberately bypasses the
cache on disk. That makes it slower than a real build, not faster.

## Build for real

```
python scripts/build_site.py
python -m http.server 8000
```

Then open <http://localhost:8000> in a browser. The build writes into the repository root,
which is where the generated files are meant to live, so images and stylesheets all resolve
correctly.

Review what changed before committing:

```
git status
git diff -- index.html
```

## Test the two things that matter

**With JavaScript turned off**, the landing page must still list every repository, and clicking
a card title must open a full page with the README on it. That is the whole point of the
change; if it fails, the page is back to where it started.

**With JavaScript turned on**, check that:

- Typing in the search box filters the grid.
- Clicking a card opens the slide-in panel.
- The Escape key and the browser Back button both close the panel.
- Ctrl-click or middle-click on a card title opens the repository page in a new tab instead of
  opening the panel.

## About the rate limit

Without a token, GitHub allows 60 requests an hour from one address. A full build uses about
55, so two builds in the same hour will fail partway with a clear message. Nothing is written
when that happens, so the site on disk stays as it was.

If you build often, set a token first. Any classic or fine-grained token with **no scopes at
all** works, because everything the build reads is public:

```
export GH_TOKEN=your_token_here        # PowerShell: $env:GH_TOKEN = "your_token_here"
```

That raises the limit to 5,000 requests an hour and lets the build fetch repositories in
parallel. Never commit a token.

## Conclusion

`--dry-run` to look, plain `python scripts/build_site.py` to write, then a local web server to
check the result. Test with JavaScript off as well as on.

## Additional resources

+ [Architecture](../architecture.md)
+ [Troubleshooting](../troubleshooting.md)
+ [How to add a repository preview image](add-a-repo-preview-image.md)
+ [Managing personal access tokens on GitHub](https://docs.github.com/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

[Back to the project README](../../README.md)
