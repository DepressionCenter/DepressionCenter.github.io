#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# resize_thumbs.py - Resize and compress all repository preview thumbnails ending in -thumb.png.
# Author(s): Gabriel Mongefranco.
# Created: 2026-05-20
# Last Modified: 2026-09-01
# Summary: Crop images to 16:9, resize them to a maximum width of 360px, and save as optimized PNG.
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
"""Normalize the hand-made thumbnails kept in images/repo-previews/.

Run this after adding a new -thumb.png by hand. Images pulled automatically from other
repositories are normalized by build_site.py instead and land in the remote/ subfolder.
"""

import sys
from pathlib import Path

from PIL import Image

from imagelib import THUMB_MAX_WIDTH, normalize_preview, save_png

### Load Configuration ###

ROOT = Path(__file__).resolve().parent.parent
PATTERN = "images/repo-previews/*-thumb.png"

### Retrieve Source Data ###

files = sorted(ROOT.glob(PATTERN))
if not files:
    print("No matching files found for pattern:", PATTERN)
    sys.exit(0)

### Transform and Save ###

processed = 0
for path in files:
    try:
        image = Image.open(path)
    except Exception as error:
        print(f"Skipping {path}: cannot open ({error})")
        continue

    try:
        width, height = save_png(normalize_preview(image, THUMB_MAX_WIDTH), path)
        print(f"Processed {path} -> {width}x{height}")
        processed += 1
    except Exception as error:
        print(f"Failed to save {path}: {error}")

print(f"Done. Processed {processed}/{len(files)} files.")
