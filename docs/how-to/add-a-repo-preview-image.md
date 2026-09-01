<!--
This file is part of Eisenberg Family Depression Center Open Source Hub
Copyright © 2026 The Regents of the University of Michigan
Licensed under the GNU Free Documentation License v1.3 or later.
See <https://www.gnu.org/licenses/fdl-1.3.html>. See README for full license information.
-->

# Eisenberg Family Depression Center: Open Source Projects

## How to Add a Repository Preview Image

[Back to the project README](../../README.md)

Every repository card on the Open Source Hub shows a picture. This page explains the three
places that picture can come from, which one wins, and what size to make it. Follow the first
option if you can: it keeps the image next to the code it belongs to.

## Option 1: Put the image in the repository itself (preferred)

Add these two files to the repository you want to show off:

| File | Size | Purpose |
| --- | --- | --- |
| `images/Repo-preview.png` | 912 × 513 pixels | The large image on the repository's page and in the panel. |
| `images/Repo-preview-thumb.png` | 360 × 202 pixels | The small image on the card. |

Both must be 16:9. If your image is a different shape, the build centre-crops it rather than
squashing it, so keep the important part in the middle.

You only need the large one. If there is no thumbnail file, the build makes a thumbnail from
the large image.

The build also accepts these names, in this order, in the `images/` folder or at the root of
the repository:

1. `Repo-preview.png`
2. `<repository-name>.png`

Both may use `.png`, `.jpg`, `.jpeg`, or `.gif` instead. Animated GIFs keep only their first
frame, so the card does not move on its own. Files larger than 8 MB are skipped.

**One catch.** Repositories created from
[EFDC-Repo-Template](https://github.com/DepressionCenter/EFDC-Repo-Template) already contain a
stand-in `Repo-preview.png`. The build recognizes that untouched placeholder and ignores it, so
a repository that never replaced it does not lose the hand-made thumbnail described below.
Replace the file with a real screenshot and it will be picked up on the next build.

## Option 2: Add a hand-made thumbnail to this repository

Use this when you cannot change the other repository, or when the screenshot in it is not
flattering.

1. Save two files in `images/repo-previews/`:
   - `<RepositoryName>.png` at 912 × 513
   - `<RepositoryName>-thumb.png` at 360 × 202
2. Match the repository name exactly, including capital letters.
3. Run the resize scripts to make sure the proportions are right:

```
python scripts/resize_nonthumbs.py
python scripts/resize_thumbs.py
```

These scripts only touch `images/repo-previews/`. They never change images the build
downloaded, which live in `images/repo-previews/remote/`.

## Option 3: Do nothing

A repository with no image anywhere gets a card showing its initials on a dark background. That
is a reasonable placeholder, not a bug.

## Which one wins

The build checks in this order and stops at the first one it finds:

1. The repository's own image.
2. The hand-made thumbnail in `images/repo-previews/`.
3. The initials placeholder.

## How to check what happened

After a build, open `data/repos.json` and find your repository. The `image_source` field says
which option was used:

| Value | Meaning |
| --- | --- |
| `remote` | The repository's own image was used. |
| `local` | A hand-made thumbnail in this repository was used. |
| `placeholder` | No image was found; the card shows initials. |

The build also prints the same information as it runs, one line per repository.

## Conclusion

Put the image in the repository it describes whenever you can, at 912 × 513 with a 360 × 202
thumbnail. Fall back to a hand-made thumbnail here when you cannot. Check `data/repos.json` if
the result is not what you expected.

## Additional resources

+ [EFDC repository template](https://github.com/DepressionCenter/EFDC-Repo-Template)
+ [Data flow](../data-flow.md)
+ [Troubleshooting](../troubleshooting.md)
+ [How to run the build locally](run-the-build-locally.md)

[Back to the project README](../../README.md)
