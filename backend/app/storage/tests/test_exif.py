import io

import pytest
from PIL import Image

from app.storage.exif import ImageValidationError, validate_and_strip


def _make_jpeg(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGBA", (width, height), color=(0, 128, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_valid_jpeg():
    data = _make_jpeg()
    result = validate_and_strip(data, "image/jpeg")
    assert result.content_type == "image/jpeg"
    assert result.width == 100
    assert result.height == 100
    assert len(result.data) > 0


def test_valid_png():
    data = _make_png()
    result = validate_and_strip(data, "image/png")
    assert result.content_type == "image/png"
    assert result.width == 100
    assert result.height == 100


def test_rejects_svg():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    with pytest.raises(ImageValidationError, match="Unsupported"):
        validate_and_strip(svg, "image/svg+xml")


def test_rejects_oversized():
    large = _make_jpeg(2000, 2000)
    with pytest.raises(ImageValidationError, match="exceeds"):
        validate_and_strip(large, "image/jpeg", max_bytes=1000)


def test_rejects_invalid_bytes():
    with pytest.raises(ImageValidationError, match="Invalid image"):
        validate_and_strip(b"not an image", "image/jpeg")
