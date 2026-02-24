"""
Searchable PDF generator using reportlab.
- Original image rendered as full-page background
- Invisible text layer positioned using Tesseract bounding boxes
- Result: Ctrl+F searchable PDF
"""
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
from app.services.ocr import PageOCRResult


def _pt(pixels: int, dpi: int = 96) -> float:
    """Convert pixel count to PDF points (1 pt = 1/72 inch)."""
    return pixels * 72.0 / dpi


def generate_searchable_pdf(
    pages: list[tuple[Image.Image, PageOCRResult]],
    output_path: str,
) -> None:
    """
    Build a multi-page searchable PDF.

    Args:
        pages: list of (original_rgb_image, ocr_result) per page
        output_path: destination .pdf file path
    """
    if not pages:
        raise ValueError("No pages provided for PDF generation.")

    # Use first page dimensions to set canvas size (we'll vary per page)
    first_img, _ = pages[0]
    first_w, first_h = first_img.size
    page_w_pt = _pt(first_w)
    page_h_pt = _pt(first_h)

    c = canvas.Canvas(output_path, pagesize=(page_w_pt, page_h_pt))

    for original_img, ocr_result in pages:
        img_w, img_h = original_img.size
        pw = _pt(img_w)
        ph = _pt(img_h)

        c.setPageSize((pw, ph))

        # Draw original image as full background
        img_buffer = io.BytesIO()
        original_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=pw, height=ph)

        # Invisible text overlay aligned to Tesseract bounding boxes
        # reportlab origin is bottom-left; image origin is top-left — flip y
        for wb in ocr_result.word_boxes:
            if not wb.text.strip() or wb.confidence < 20:
                continue

            # Scale from OCR image pixels to original image pixels
            scale_x = img_w / ocr_result.image_width
            scale_y = img_h / ocr_result.image_height

            x_px = wb.left * scale_x
            y_px = wb.top * scale_y
            w_px = wb.width * scale_x
            h_px = wb.height * scale_y

            # Convert to PDF points, flip y
            x_pt = _pt(x_px)
            y_pt = ph - _pt(y_px) - _pt(h_px)
            font_size = max(4, _pt(h_px) * 0.9)

            c.setFont("Helvetica", font_size)
            c.setFillColorRGB(0, 0, 0, alpha=0)  # fully transparent text
            c.drawString(x_pt, y_pt, wb.text)

        c.showPage()

    c.save()
