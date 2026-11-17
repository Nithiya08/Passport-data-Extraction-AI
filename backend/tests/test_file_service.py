"""Unit tests for file validation, PDF-to-image conversion, and image optimization."""

import io
import pytest
from PIL import Image
from fastapi import UploadFile, HTTPException
from app.services.file_service import (
    is_valid_pdf_magic,
    is_valid_image_magic,
    resize_image_bytes,
    validate_and_process_uploads
)


def create_test_image(format="JPEG", size=(100, 100)) -> bytes:
    """Helper to generate in-memory valid image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(100, 150, 200))
    img.save(buf, format=format)
    return buf.getvalue()


def test_is_valid_pdf_magic():
    """Verify detection of PDF magic bytes."""
    valid_pdf = b"%PDF-1.4\n..."
    invalid_pdf = b"NOT A PDF..."

    assert is_valid_pdf_magic(valid_pdf) is True
    assert is_valid_pdf_magic(invalid_pdf) is False


def test_is_valid_image_magic():
    """Verify image magic bytes and integrity check."""
    jpeg_bytes = create_test_image("JPEG")
    png_bytes = create_test_image("PNG")
    fake_bytes = b"Just plain text disguised as an image"

    is_jpeg, fmt1 = is_valid_image_magic(jpeg_bytes)
    assert is_jpeg is True
    assert fmt1 == "jpeg"

    is_png, fmt2 = is_valid_image_magic(png_bytes)
    assert is_png is True
    assert fmt2 == "png"

    is_fake, _ = is_valid_image_magic(fake_bytes)
    assert is_fake is False


def test_resize_oversized_image():
    """Verify large images are downsampled to within max_side."""
    large_bytes = create_test_image("JPEG", size=(3000, 2400))
    resized = resize_image_bytes(large_bytes, max_side=2000)

    with Image.open(io.BytesIO(resized)) as img:
        assert max(img.size) <= 2000
        assert img.format == "JPEG"


def test_validate_and_process_uploads_success():
    """Verify processing of valid uploaded images."""
    jpeg_bytes = create_test_image("JPEG", size=(800, 600))
    upload = UploadFile(
        filename="passport.jpg",
        file=io.BytesIO(jpeg_bytes),
        headers={"content-type": "image/jpeg"}
    )

    processed = validate_and_process_uploads([upload])
    assert len(processed) == 1
    assert len(processed[0]) > 0


def test_validate_empty_file_fails():
    """Verify rejection when uploaded file is empty."""
    upload = UploadFile(
        filename="empty.jpg",
        file=io.BytesIO(b""),
        headers={"content-type": "image/jpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_and_process_uploads([upload])
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_validate_invalid_format_fails():
    """Verify rejection when file content is not an image or PDF."""
    fake_bytes = b"MZ\x90\x00\x03\x00\x00\x00"  # Executable header
    upload = UploadFile(
        filename="malicious.jpg",
        file=io.BytesIO(fake_bytes),
        headers={"content-type": "image/jpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_and_process_uploads([upload])
    assert exc_info.value.status_code == 400
    assert "not a valid" in exc_info.value.detail.lower()

