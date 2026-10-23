import logging
import os
import shutil
from functools import lru_cache
from pathlib import Path

import pytesseract
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_TESSDATA_DIR = BACKEND_DIR / "tessdata"

# Where the Windows installers put tesseract.exe when it is not on PATH.
WINDOWS_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
]


@lru_cache(maxsize=1)
def find_tesseract() -> str | None:
    candidates = [settings.TESSERACT_CMD, shutil.which("tesseract"), *WINDOWS_TESSERACT_PATHS]

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)

    return None


@lru_cache(maxsize=1)
def ocr_config() -> tuple[str, str]:
    """(language string, extra tesseract config) for the languages actually installed."""
    tesseract = find_tesseract()

    if tesseract is None:
        raise HTTPException(
            status_code=500,
            detail="Tesseract OCR is not installed, so images cannot be read. "
            "Install it from https://github.com/UB-Mannheim/tesseract/wiki",
        )

    pytesseract.pytesseract.tesseract_cmd = tesseract

    tessdata_dir = Path(settings.TESSDATA_DIR) if settings.TESSDATA_DIR else PROJECT_TESSDATA_DIR
    config = ""

    if tessdata_dir.is_dir():
        # An environment variable, not --tessdata-dir: pytesseract keeps the
        # quotes of a quoted path on Windows, which breaks the lookup.
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

    available = set(pytesseract.get_languages(config=config))
    wanted = [language for language in settings.OCR_LANGUAGES.split("+") if language]
    languages = [language for language in wanted if language in available]
    missing = [language for language in wanted if language not in available]

    if missing:
        logger.warning("OCR languages not installed, skipping: %s", ", ".join(missing))

    if not languages:
        languages = ["eng"] if "eng" in available else sorted(available - {"osd"})[:1]

    logger.info("OCR ready: %s, languages=%s", tesseract, "+".join(languages))
    return "+".join(languages), config


def extract_text_from_pil_image(image: Image.Image) -> str:
    languages, config = ocr_config()

    # Tesseract reads greyscale more reliably than colour or transparent images.
    return pytesseract.image_to_string(image.convert("L"), lang=languages, config=config).strip()


def extract_text_from_image(file_path: Path) -> str:
    try:
        with Image.open(file_path) as image:
            return extract_text_from_pil_image(image)

    except HTTPException:
        raise

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image could not be opened. Please upload a valid image file.",
        )

    except Exception:
        logger.exception("OCR failed for %s", file_path.name)
        raise HTTPException(
            status_code=500,
            detail="The text in this image could not be read.",
        )
