"""UDFs for the bonsai label round-trip. Pure Python; no table imports."""

from __future__ import annotations

import PIL.Image

import pixeltable as pxt

# A canopy pixel is clearly green: G dominates both R and B by this margin.
GREEN_MARGIN = 30


@pxt.udf
def canopy_bbox(photo: PIL.Image.Image) -> list[int]:
    """Bounding box [x, y, w, h] of the green canopy in a specimen photo (COCO bbox order)."""
    rgb = photo.convert('RGB')
    w, h = rgb.size
    px = rgb.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if g - r > GREEN_MARGIN and g - b > GREEN_MARGIN:
                xs.append(x)
                ys.append(y)
    if not xs:
        return [0, 0, 0, 0]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]
