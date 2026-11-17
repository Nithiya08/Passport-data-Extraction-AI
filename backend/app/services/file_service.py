"""File validation, PDF-to-image conversion, and image optimization service."""

import io
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import fitz  # PyMuPDF
from app.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def is_valid_pdf_magic(data: bytes) -> bool:
    """Check if byte stream starts with the PDF header magic bytes '%PDF-'."""
    return data[:5] == b"%PDF-"


def is_valid_image_magic(data: bytes) -> Tuple[bool, str]:
    """Inspect magic bytes and use Pillow to verify image validity and format.

    Returns:
        (is_valid, detected_format)
    """
    if len(data) < 12:
        return False, ""

    # Check common magic headers
    # JPEG: FF D8 FF
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    # WEBP: 'RIFF'....'WEBP'
    is_jpeg = data.startswith(b"\xff\xd8\xff")
    is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = data.startswith(b"RIFF") and data[8:12] == b"WEBP"

    if not (is_jpeg or is_png or is_webp):
        return False, ""

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
            fmt = img.format.lower() if img.format else ""
            if fmt in ("jpeg", "jpg", "png", "webp"):
                return True, fmt
    except Exception:
        return False, ""

    return False, ""


def enhance_damaged_document(img: Image.Image) -> Image.Image:
    """Forensic image enhancement for degraded, faded, or low-contrast passport scans.

    Enhancements applied:
    1. Autocontrast stretching (removes yellowed paper tint and normalizes dynamic range).
    2. Unsharp Masking (recovers blurred/faded character edges and stamp boundaries).
    3. Micro-contrast boost (separates faint ink from noisy paper texture).
    """
    if img.mode != "RGB":
        rgb = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        rgb.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = rgb

    # 1. Autocontrast stretching (cutoff=0.5% ignores scanner margin outliers)
    enhanced = ImageOps.autocontrast(img, cutoff=0.5)

    # 2. Unsharp Masking for character edge definition
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))

    # 3. Fine contrast boost
    enhancer = ImageEnhance.Contrast(enhanced)
    enhanced = enhancer.enhance(1.15)

    return enhanced


def resize_image_bytes(image_bytes: bytes, max_side: int = 2000, enhance: bool = True) -> bytes:
    """Downsample image if width or height exceeds max_side and apply forensic enhancement."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Convert paletted or RGBA to RGB for JPEG encoding
        if img.mode in ("RGBA", "LA", "P", "1"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        else:
            rgb_img = img.convert("RGB")

        # Resize if larger than max_side
        width, height = rgb_img.size
        if width > max_side or height > max_side:
            rgb_img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

        # Apply forensic enhancement for aged/faded text & faint stamps
        if enhance and getattr(settings, "ENABLE_FORENSIC_ENHANCEMENT", True):
            rgb_img = enhance_damaged_document(rgb_img)

        out_buffer = io.BytesIO()
        rgb_img.save(out_buffer, format="JPEG", quality=88)
        return out_buffer.getvalue()


def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 160, max_side: int = 2000) -> List[bytes]:
    """Convert each page of a PDF in memory to an optimized JPEG byte buffer.

    Fast, memory-efficient direct bridge:
    - Renders via PyMuPDF C++ engine directly at target DPI (160 DPI).
    - Bridges raw pixmap samples to Pillow without slow intermediate JPEG encode/decode cycles.
    - Applies autocontrast and micro-contrast enhancement in sub-second speeds.
    """
    image_buffers: List[bytes] = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Corrupt or unreadable PDF document: {str(exc)}"
        )

    try:
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            # Render page to pixmap at specified DPI (160 DPI is sharp and 10x faster)
            pixmap = page.get_pixmap(dpi=dpi)
            
            # Direct bridge from raw pixmap bytes to PIL (avoids double JPEG compression)
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

            if max(img.size) > max_side:
                img.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)

            # Apply forensic enhancement for aged/faded text
            if getattr(settings, "ENABLE_FORENSIC_ENHANCEMENT", True):
                img = ImageOps.autocontrast(img, cutoff=0.5)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)

            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=85)
            image_buffers.append(out_buf.getvalue())
    finally:
        doc.close()

    return image_buffers


def validate_and_process_uploads(files: List[UploadFile]) -> List[bytes]:
    """Validate uploaded multipart files by size and real content, returning processed JPEG byte buffers.

    Ensures:
      - File count between 1 and MAX_FILES.
      - Max file size <= MAX_FILE_SIZE_MB.
      - In-memory content verification (rejects masked/renamed binaries).
      - Converts PDFs to page-by-page images.
      - Resizes oversized images.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one passport document image or PDF is required.")

    if settings.MAX_FILES is not None and len(files) > settings.MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum allowed is {settings.MAX_FILES}, but received {len(files)}."
        )

    processed_pages: List[bytes] = []

    for file in files:
        if hasattr(file, "file") and file.file is not None:
            contents = file.file.read()
        else:
            contents = b""
        filename = file.filename or "unknown"

        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' is empty."
            )

        if settings.MAX_FILE_SIZE_MB is not None:
            max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if len(contents) > max_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{filename}' ({len(contents) / (1024*1024):.1f} MB) exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
                )

        # Content validation
        if is_valid_pdf_magic(contents):
            pdf_pages = convert_pdf_to_images(
                contents,
                dpi=settings.PDF_DPI,
                max_side=settings.MAX_IMAGE_DIMENSION
            )
            processed_pages.extend(pdf_pages)
        else:
            is_valid_img, _ = is_valid_image_magic(contents)
            if not is_valid_img:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{filename}' is not a valid JPEG, PNG, WEBP image or PDF document."
                )
            optimized = resize_image_bytes(contents, max_side=settings.MAX_IMAGE_DIMENSION)
            processed_pages.append(optimized)

    return processed_pages
