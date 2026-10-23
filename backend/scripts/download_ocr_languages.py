"""Download the Tesseract language files the app uses into backend/tessdata.

Tesseract itself must be installed separately (Windows: the UB-Mannheim build,
e.g. `winget install UB-Mannheim.TesseractOCR`). Its installer includes English
only; this adds Gujarati (and English, so the folder is complete on its own).

    python scripts/download_ocr_languages.py
"""

import urllib.request
from pathlib import Path

# Official trained models from the Tesseract project.
SOURCE = "https://github.com/tesseract-ocr/tessdata/raw/main/{language}.traineddata"
LANGUAGES = ["eng", "guj", "osd"]

TESSDATA_DIR = Path(__file__).resolve().parents[1] / "tessdata"


def main() -> None:
    TESSDATA_DIR.mkdir(exist_ok=True)

    for language in LANGUAGES:
        target = TESSDATA_DIR / f"{language}.traineddata"

        if target.exists():
            print(f"{language}: already present")
            continue

        print(f"{language}: downloading...")
        urllib.request.urlretrieve(SOURCE.format(language=language), target)
        print(f"{language}: {target.stat().st_size / 1_048_576:.1f} MB")


if __name__ == "__main__":
    main()
