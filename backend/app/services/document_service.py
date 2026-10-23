from pathlib import Path
import shutil
import uuid
import logging

from fastapi import UploadFile , HTTPException
from fastapi.concurrency import run_in_threadpool

from app.repositories.document_repository import save_document_analysis
from app.ai.pipeline import analyze_document_text
from app.document_processing.docx_extractor import extract_text_from_docx
from app.document_processing.file_validator import validate_uploaded_file
from app.document_processing.image_ocr import extract_text_from_image
from app.document_processing.pdf_extractor import extract_text_from_pdf
from app.document_processing.text_extractor import extract_text_from_txt

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
TEXT_PREVIEW_CHARS = 600
# The full masked text is stored so every finding can be shown in context.
MAX_STORED_TEXT_CHARS = 200_000


def create_safe_filename(original_filename: str) -> str:
    file_extension = Path(original_filename).suffix.lower()
    unique_name = uuid.uuid4().hex

    return f"{unique_name}{file_extension}"


def extract_text_by_file_type(file_path: Path, file_extension: str) -> str:
    if file_extension == ".txt":
        return extract_text_from_txt(file_path)

    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if file_extension == ".docx":
        return extract_text_from_docx(file_path)

    if file_extension in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(file_path)

    return ""


async def save_uploaded_document(file: UploadFile , current_user : dict) -> dict:
    try:
        original_filename, file_extension = await validate_uploaded_file(file)

        logger.info("Uploading document: %s", original_filename)

        UPLOAD_DIR.mkdir(exist_ok=True)

        stored_filename = create_safe_filename(original_filename)
        file_path = UPLOAD_DIR / stored_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR and the AI model are slow, blocking work: run them in a worker
        # thread so other requests are not frozen meanwhile.
        try:
            extracted_text = await run_in_threadpool(
                extract_text_by_file_type, file_path, file_extension
            )
        finally:
            # Only the masked analysis is kept; the original file is not stored.
            file_path.unlink(missing_ok=True)

        logger.info(
            "Extracted %s characters from %s",
            len(extracted_text),
            original_filename,
        )

        analysis_result = await run_in_threadpool(analyze_document_text, extracted_text)
        redacted_text = analysis_result["redacted_text"]

        response_data = {
            "message": "File uploaded successfully",
            "filename": original_filename,
            "stored_filename": stored_filename,
            "text_extracted": bool(extracted_text),
            "character_count": len(extracted_text),
            "text_preview": redacted_text[:TEXT_PREVIEW_CHARS],
            "summary": analysis_result["summary"],
            "keyword_analysis": analysis_result["keyword_analysis"],
            "sensitive_info_analysis": analysis_result["sensitive_info_analysis"],
            "policy_violation_analysis": analysis_result["policy_violation_analysis"],
            "threat_analysis": analysis_result["threat_analysis"],
            "anomaly_analysis": analysis_result["anomaly_analysis"],
            "indian_compliance_analysis": analysis_result["indian_compliance_analysis"],
            "tampering_analysis": analysis_result["tampering_analysis"],
            "risk_analysis": analysis_result["risk_analysis"],
            "uploaded_by": current_user["user_id"],
            "uploaded_by_email": current_user["email"],
            "risk_report": analysis_result["risk_report"],
            "document_heatmap": analysis_result["document_heatmap"],
            "semantic_analysis": analysis_result["semantic_analysis"],
            "findings": analysis_result["findings"],
            "document_text": redacted_text[:MAX_STORED_TEXT_CHARS],
            "document_text_truncated": len(redacted_text) > MAX_STORED_TEXT_CHARS,
        }

        document_id = await save_document_analysis(response_data)

        logger.info("Saved document analysis with ID: %s", document_id)

        response_data["document_id"] = document_id

        return response_data

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Document upload analysis failed")

        raise HTTPException(
            status_code=500,
            detail="The document could not be processed.",
        )