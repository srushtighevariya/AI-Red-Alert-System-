from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".txt"}


async def validate_uploaded_file(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename",
        )

    original_filename = Path(file.filename).name
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed types: PDF, DOCX, PNG, JPG, JPEG, TXT",
        )

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    return original_filename, file_extension