#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# imagelib.py - Shared cropping and resizing helpers for repository preview images.
# Author(s): Gabriel Mongefranco.
# Created: 2026-09-01
# Last Modified: 2026-09-01
# Summary: Centre-crop images to 16:9 and resize them to the site's standard preview widths,
#          so preview images always have identical proportions no matter where they came from.
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
"""Cropping and resizing helpers shared by the preview-image scripts and the site build.

The site shows every repository preview in a 16:9 box. Images that arrive with different
proportions are centre-cropped rather than squashed, because squashing distorts screenshots
of text and makes them hard to read.
"""

from pathlib import Path

from PIL import Image, ImageOps

### Configuration ###

# Widths the site uses. Heights are derived from the aspect ratio so the two can never drift.
FULL_MAX_WIDTH = 912
THUMB_MAX_WIDTH = 360
ASPECT_RATIO = 16 / 9

# Upper bound on decoded pixels, as a guard against decompression-bomb images from other
# repositories. 80 megapixels is far beyond any legitimate screenshot.
Image.MAX_IMAGE_PIXELS = 80_000_000


def height_for_width(width):
    """Return the 16:9 height that pairs with the given width.

    Args:
        width: Target width in pixels.

    Returns:
        int: Height in pixels, rounded to the nearest whole pixel.
    """
    return round(width / ASPECT_RATIO)


def crop_to_aspect(image, aspect=ASPECT_RATIO):
    """Centre-crop an image to the given aspect ratio.

    Whichever dimension is proportionally too large is trimmed equally from both sides, so
    the subject of a screenshot stays in view.

    Args:
        image: A PIL Image.
        aspect: Desired width divided by height. Defaults to 16:9.

    Returns:
        PIL.Image.Image: The cropped image, or the original when it already matches.
    """
    width, height = image.size
    if height == 0:
        return image

    current = width / height
    if abs(current - aspect) <= 1e-6:
        return image

    if current > aspect:
        # Too wide: trim the left and right edges.
        new_width = int(height * aspect)
        left = (width - new_width) // 2
        box = (left, 0, left + new_width, height)
    else:
        # Too tall: trim the top and bottom edges.
        new_height = int(width / aspect)
        top = (height - new_height) // 2
        box = (0, top, width, top + new_height)
    return image.crop(box)


def normalize_preview(image, max_width, allow_upscale=False):
    """Crop an image to 16:9 and scale it down to at most ``max_width`` pixels wide.

    Small images are left at their own width by default. Upscaling a 200px screenshot to
    912px only makes it blurry, so it is off unless the caller asks for it.

    Args:
        image: A PIL Image.
        max_width: Largest width to produce, in pixels.
        allow_upscale: When True, images narrower than max_width are enlarged to match it.

    Returns:
        PIL.Image.Image: A 16:9 image no wider than max_width.
    """
    image = ImageOps.exif_transpose(image)  # Honors the rotation flag digital cameras set
    image = crop_to_aspect(image)

    width, _ = image.size
    target_width = max_width if allow_upscale else min(max_width, width)
    target_height = height_for_width(target_width)

    if image.size == (target_width, target_height):
        return image
    return image.resize((target_width, target_height), Image.LANCZOS)


def flatten_for_png(image):
    """Convert any input mode to something ``PNG`` can store without surprises.

    Palette images with transparency (the usual GIF case) become RGBA; everything else that
    is not already RGB or RGBA becomes RGB. Animated inputs keep only their first frame,
    because a card that animates on its own would violate the motion rules in the project's
    accessibility standard.

    Args:
        image: A PIL Image, possibly animated or palette-based.

    Returns:
        PIL.Image.Image: A single-frame image in RGB or RGBA mode.
    """
    if getattr(image, "n_frames", 1) > 1:
        image.seek(0)

    if image.mode in ("RGB", "RGBA"):
        return image
    if image.mode in ("P", "LA", "PA") and "transparency" in image.info:
        return image.convert("RGBA")
    if image.mode == "RGBa":
        return image.convert("RGBA")
    return image.convert("RGB")


def save_png(image, path):
    """Write an image to disk as an optimized PNG, creating parent folders as needed.

    Args:
        image: A PIL Image.
        path: Destination path. The extension is not changed; callers pass a .png path.

    Returns:
        tuple[int, int]: The width and height actually written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True, compress_level=6)
    return image.size
