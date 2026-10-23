# AI Document Red Alert Detection System

## Project Overview

AI Document Red Alert Detection System is an AI-powered web application that scans uploaded documents and detects suspicious, sensitive, fraudulent, threatening, or policy-violating content.

The system extracts text from uploaded files, analyzes the content using NLP and rule-based AI detection methods, generates a risk score, assigns an alert level, highlights suspicious sections, and stores document history for future review.

## Area of Study

This project belongs to the following areas:

- Artificial Intelligence
- Natural Language Processing
- Document Intelligence
- Cybersecurity
- Information Security
- Fraud Detection
- OCR-Based Text Analysis

## Key Features

- User registration and JWT login
- PDF, DOCX, TXT, and image upload
- OCR for photos and scanned PDFs (English + Gujarati)
- English and Gujarati risky content detection
- Suspicious keyword detection
- Sensitive information detection
- Threat language detection
- Policy violation detection
- Indian compliance data detection
- Tampered or abnormal text detection
- Risk score generation
- Green, Yellow, and Red alert classification
- AI model (multilingual mDeBERTa) that detects risky meaning even without keywords
- Key-sentence summary (TextRank) plus a plain-language "what we found" summary
- Personal data masked everywhere it is stored or shown; uploaded files are not kept
- Highlighted suspicious sections
- Document history
- Admin panel
- Dashboard analytics and charts

## Alert Levels

| Risk Score | Alert Level |
|---|---|
| 0-30 | Green |
| 31-70 | Yellow |
| 71-100 | Red |

## Tech Stack

### Backend

- Python
- FastAPI
- MongoDB
- PyMongo Async
- JWT Authentication
- Pydantic
- pdfplumber
- python-docx
- pytesseract
- Pillow

### Frontend

- React
- Vite
- Axios
- Lucide React
- Recharts
- CSS

### AI/NLP

- Rule-based detection (whole-word phrase matching, English + Gujarati)
- Checksum validation for card (Luhn) and Aadhaar (Verhoeff) numbers
- Zero-shot NLI model: MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
- Extractive TextRank summarisation
- Regular expressions
- OCR text extraction
- Risk scoring engine

## Project Structure

```text
ai-document-red-alert-project
├── backend
│   ├── app
│   │   ├── ai
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── document_processing
│   │   ├── repositories
│   │   ├── schemas
│   │   ├── services
│   │   └── main.py
│   ├── uploads
│   ├── requirements.txt
│   └── .env
├── frontend
│   ├── src
│   │   ├── api
│   │   ├── pages
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── .env
├── sample_documents
└── README.md`

### How the System Works
- User logs in using JWT authentication.
- User uploads a document.
- Backend validates the file type and size.
- Text is extracted from the document.
- OCR is applied if the file is an image.
- AI pipeline analyzes the extracted text.
- Risk score is calculated.
- Alert level is assigned.
- Suspicious sections are highlighted.
- Result is stored in MongoDB.
- React dashboard displays the analysis.

## Setup

```bat
:: Python packages (from the project root)
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements-dev.txt

:: Optional AI model (~1.5 GB with PyTorch; the model downloads on first start)
.venv\Scripts\python -m pip install -r backend\requirements-ml.txt --extra-index-url https://download.pytorch.org/whl/cpu

:: OCR: install Tesseract, then fetch the Gujarati language file
winget install UB-Mannheim.TesseractOCR
.venv\Scripts\python backend\scripts\download_ocr_languages.py

:: Frontend packages
cd frontend && npm install
```

Then double-click **`START_PROJECT.bat`** — it starts MongoDB (if needed), the
backend and the frontend, and opens http://localhost:5173.

Without the AI packages or Tesseract the app still runs: the rule-based
detectors work on PDF, DOCX and TXT files.

### Settings (`backend/.env`)

| Setting | Default | Meaning |
|---|---|---|
| `ENABLE_SEMANTIC_MODEL` | `true` | Use the AI model on top of the rules |
| `SEMANTIC_THRESHOLD` | `0.75` | How sure the model must be (0–1) before a signal counts |
| `OCR_LANGUAGES` | `eng+guj` | Tesseract languages |
| `TESSERACT_CMD` | *(auto)* | Path to `tesseract.exe` if it is not found automatically |

### How the AI model is used

The model compares each part of the document with short descriptions
(threat/extortion, scam, request for passwords or PINs, hiding transactions
from auditors) and with "ordinary content". A signal counts only when the model
is at least 75% sure, and only for risks the rules did not already find. On its
own the model can raise a document to **Yellow** (review), never to **Red**.

On hand-written test sentences it caught 5 of 9 paraphrased risks that contain
no keywords, without flagging any of the safe examples. It is an extra signal,
not a replacement for human review; a model fine-tuned on real labelled
documents would do better.

## Tests

```bat
cd backend
..\.venv\Scripts\python -m pytest -q tests
..\.venv\Scripts\python scripts\evaluate_sample_dataset.py
```

## Privacy maintenance

Documents analysed before masking was added may still contain raw personal
data. Preview, then apply:

```bat
cd backend
..\.venv\Scripts\python scripts\redact_existing_documents.py
..\.venv\Scripts\python scripts\redact_existing_documents.py --apply
```

