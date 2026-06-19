"""Set-of-Marks screenshot annotation for desktop vision.

Draws numbered bounding boxes over UI regions so the vision LLM can
reference elements by their mark number.  Adapted from browser/highlight.py.

For the Layer 3 vision loop we send the raw screenshot to the vision LLM
and ask it to return pixel coordinates directly — we don't need SoM marks
for coordinate-based interaction.  This module is kept for completeness
and for any future use where we want to annotate regions before sending
to the LLM (e.g. when we want the model to pick a mark number rather than
a coordinate).
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import NamedTuple


class Mark(NamedTuple):
    index: int
    x: int      # window-relative pixel left
    y: int      # window-relative pixel top
    w: int      # width
    h: int      # height
    label: str  # display label


def annotate(
    image_path: str,
    marks: list[Mark],
    out_path: str | None = None,
) -> str:
    """Draw numbered bounding boxes on *image_path* and save to *out_path*.

    Returns the path to the annotated image.
    Requires Pillow (``pip install pillow``).
    """
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    colors = [
        "#E63946", "#2196F3", "#2ECC71", "#FF9800", "#9C27B0",
        "#00BCD4", "#FF5722", "#795548",
    ]

    for mark in marks:
        if mark.w == 0 or mark.h == 0:
            continue  # placeholder mark with no coords
        color = colors[mark.index % len(colors)]
        # Bounding box
        draw.rectangle(
            [mark.x, mark.y, mark.x + mark.w, mark.y + mark.h],
            outline=color,
            width=2,
        )
        # Badge
        badge = str(mark.index)
        try:
            bbox = draw.textbbox((0, 0), badge, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            # Older Pillow versions
            tw, th = draw.textsize(badge, font=font)  # type: ignore[attr-defined]
        pad = 2
        bx = mark.x
        by = mark.y - th - pad * 2
        if by < 0:
            by = mark.y + 2
        draw.rectangle([bx, by, bx + tw + pad * 2, by + th + pad * 2], fill=color)
        draw.text((bx + pad, by + pad), badge, fill="white", font=font)

    dest = out_path or str(Path(image_path).with_suffix("")) + "_som.png"
    img.save(dest)
    return dest


def image_to_data_url(image_path: str) -> str:
    """Read a PNG/JPEG and return a base64 data URL suitable for /v1/vision."""
    path = Path(image_path)
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"
