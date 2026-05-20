#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# resize_thumbs.py - Resize and compress all repository preview thumbnails ending in -thumb.png.
# Author(s): Gabriel Mongefranco.
# Created: 2026-05-20
# Last Modified: 2026-05-20
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
from PIL import Image
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
PATTERN = "images/repo-previews/**/*-thumb.png"

files = sorted(ROOT.glob(PATTERN))
if not files:
    print("No matching files found for pattern:", PATTERN)
    sys.exit(0)

processed = 0
for p in files:
    try:
        im = Image.open(p)
    except Exception as e:
        print(f"Skipping {p}: cannot open ({e})")
        continue

    w, h = im.size
    target_w = min(360, w)
    target_h = round(target_w * 9 / 16)

    desired_ratio = 16 / 9
    orig_ratio = w / h
    if abs(orig_ratio - desired_ratio) > 1e-6:
        if orig_ratio > desired_ratio:
            new_w = int(h * desired_ratio)
            left = (w - new_w) // 2
            box = (left, 0, left + new_w, h)
        else:
            new_h = int(w / desired_ratio)
            top = (h - new_h) // 2
            box = (0, top, w, top + new_h)
        im = im.crop(box)

    im = im.resize((target_w, target_h), Image.LANCZOS)

    try:
        im.save(p, format="PNG", optimize=True, compress_level=6)
        print(f"Processed {p} -> {target_w}x{target_h}")
        processed += 1
    except Exception as e:
        print(f"Failed to save {p}: {e}")

print(f"Done. Processed {processed}/{len(files)} files.")
