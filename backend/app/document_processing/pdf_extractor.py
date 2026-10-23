import logging
from pathlib import Path

import pdfplumber
import pypdfium2

from app.document_processing.image_ocr import extract_text_from_pil_image

logger = logging.getLogger(__name__)

# A PDF with less text than this is treated as scanned (pages are images).
MIN_TEXT_CHARS = 20
MAX_OCR_PAGES = 10
OCR_RENDER_SCALE = 2.5  # ~180 DPI, enough for Tesseract without being slow


def extract_text_from_pdf(file_path: Path) -> str:
    extracted_pages = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(page_text.strip())

    text = "\n\n".join(extracted_pages)

    if len(text.strip()) >= MIN_TEXT_CHARS:
        return text

    logger.info("%s has no text layer; reading it with OCR", file_path.name)
    return extract_text_from_scanned_pdf(file_path)


def extract_text_from_scanned_pdf(file_path: Path) -> str:
    pdf = pypdfium2.PdfDocument(str(file_path))
    pages = []

    try:
        for index in range(min(len(pdf), MAX_OCR_PAGES)):
            image = pdf[index].render(scale=OCR_RENDER_SCALE).to_pil()
            page_text = extract_text_from_pil_image(image)

            if page_text:
                pages.append(page_text)
    finally:
        pdf.close()

    return "\n\n".join(pages)
