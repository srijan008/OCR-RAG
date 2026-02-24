"""
OCR service using Tesseract (pytesseract).
Extracts text with bounding boxes and confidence scores per page.
"""
import pytesseract
from PIL import Image
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
from app.config import get_settings

settings = get_settings()

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


@dataclass
class WordBox:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float


@dataclass
class PageOCRResult:
    page_number: int
    text: str
    word_boxes: list[WordBox]
    avg_confidence: float
    image_width: int
    image_height: int


def extract_page(preprocessed_img: Image.Image, page_number: int = 1) -> PageOCRResult:
    """
    Run Tesseract on a single preprocessed PIL image.
    Returns structured OCR result with bounding boxes and confidence.
    """
    w, h = preprocessed_img.size

    # Full text extraction
    full_text = pytesseract.image_to_string(
        preprocessed_img,
        config="--psm 3 --oem 3",  # Auto page segmentation, LSTM engine
    ).strip()

    # Detailed data with bounding boxes and confidence
    data = pytesseract.image_to_data(
        preprocessed_img,
        config="--psm 3 --oem 3",
        output_type=pytesseract.Output.DICT,
    )

    word_boxes: list[WordBox] = []
    confidences: list[float] = []

    for i, word_text in enumerate(data["text"]):
        conf = data["conf"][i]
        if conf == -1 or not word_text.strip():
            continue
        conf_float = float(conf)
        confidences.append(conf_float)
        word_boxes.append(
            WordBox(
                text=word_text.strip(),
                left=data["left"][i],
                top=data["top"][i],
                width=data["width"][i],
                height=data["height"][i],
                confidence=conf_float,
            )
        )

    avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0

    return PageOCRResult(
        page_number=page_number,
        text=full_text,
        word_boxes=word_boxes,
        avg_confidence=avg_conf,
        image_width=w,
        image_height=h,
    )
