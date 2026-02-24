"""
Image preprocessing pipeline:
1. Convert to grayscale
2. Deskew (Hough-line based rotation correction)
3. CLAHE contrast enhancement
4. Gaussian denoising
5. Adaptive thresholding (Otsu binarization for OCR)
"""
import numpy as np
import cv2
from PIL import Image
import io


def pil_to_cv(img: Image.Image) -> np.ndarray:
    """Convert PIL Image (RGB) to OpenCV BGR array."""
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def cv_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR array to PIL Image (RGB)."""
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def deskew(img_gray: np.ndarray) -> np.ndarray:
    """Correct skew using Hough line transform."""
    edges = cv2.Canny(img_gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
    if lines is None:
        return img_gray

    angles = []
    for line in lines[:20]:
        rho, theta = line[0]
        angle = (theta - np.pi / 2) * (180 / np.pi)
        if abs(angle) < 45:
            angles.append(angle)

    if not angles:
        return img_gray

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return img_gray

    h, w = img_gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        img_gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def enhance_contrast(img_gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE for local contrast enhancement."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(img_gray)


def denoise(img_gray: np.ndarray) -> np.ndarray:
    """Apply non-local means denoising."""
    return cv2.fastNlMeansDenoising(img_gray, h=10, templateWindowSize=7, searchWindowSize=21)


def binarize(img_gray: np.ndarray) -> np.ndarray:
    """Otsu binarization for maximum OCR accuracy."""
    _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess_image(pil_img: Image.Image) -> tuple[Image.Image, Image.Image]:
    """
    Full preprocessing pipeline.
    Returns:
        original_rgb: original (for PDF background)
        processed:    preprocessed image (for OCR input)
    """
    # Keep original at high res for PDF background
    original_rgb = pil_img.convert("RGB")

    # Ensure minimum resolution for OCR (300 DPI equivalent)
    w, h = pil_img.size
    if min(w, h) < 1000:
        scale = 1000 / min(w, h)
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    arr = pil_to_cv(pil_img)
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

    gray = deskew(gray)
    gray = enhance_contrast(gray)
    gray = denoise(gray)
    binary = binarize(gray)

    processed = Image.fromarray(binary)
    return original_rgb, processed
