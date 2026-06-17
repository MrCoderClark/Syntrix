from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image

ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class ImageValidationError(Exception):
    pass


@dataclass
class ProcessedImage:
    data: bytes
    content_type: str
    width: int
    height: int


def validate_and_strip(
    raw: bytes,
    content_type: str,
    max_bytes: int = 8_388_608,
) -> ProcessedImage:
    if content_type not in ALLOWED_MIMES:
        raise ImageValidationError(f"Unsupported content type: {content_type}")
    if len(raw) > max_bytes:
        raise ImageValidationError(f"File size {len(raw)} exceeds {max_bytes} bytes")

    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()
        img = Image.open(io.BytesIO(raw))
    except Exception as e:
        raise ImageValidationError(f"Invalid image: {e}") from e

    width, height = img.size

    output = io.BytesIO()
    fmt_map = {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
        "image/gif": "GIF",
    }
    fmt = fmt_map[content_type]
    if fmt == "JPEG":
        img.save(output, format=fmt, quality=92, optimize=True)
    elif fmt == "GIF":
        img.save(output, format=fmt, save_all=True)
    else:
        img.save(output, format=fmt, optimize=True)

    return ProcessedImage(
        data=output.getvalue(),
        content_type=content_type,
        width=width,
        height=height,
    )
