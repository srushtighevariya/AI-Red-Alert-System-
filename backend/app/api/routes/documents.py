from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query

from app.ai.findings import score_findings
from app.api.dependencies import get_current_user
from app.repositories.document_repository import (
    delete_finding_feedback,
    get_document_by_id,
    get_document_history,
    save_finding_feedback,
    update_document_review,
)
from app.schemas.document_schema import DocumentUploadResponse
from app.services.document_service import save_uploaded_document

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    return await save_uploaded_document(file , current_user)

@router.get("/history")
async def document_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    ):
    documents = await get_document_history(
        user_id=current_user["user_id"],
        limit=limit,
    )
    return {
        "message": "Document history fetched successfully",
        "count": len(documents),
        "documents": documents,
    }


async def get_accessible_document(document_id: str, current_user: dict) -> dict:
    """The document, if it exists and belongs to the user (admins can see all)."""
    document = await get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.get("uploaded_by") != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this document",
        )

    return document


@router.get("/{document_id}")
async def document_detail(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await get_accessible_document(document_id, current_user)


async def set_finding_dismissed(document_id: str, finding_id: str, dismissed: bool, current_user: dict) -> dict:
    document = await get_accessible_document(document_id, current_user)
    findings = document.get("findings")

    if not findings:
        raise HTTPException(
            status_code=409,
            detail="This document was scanned before findings could be reviewed. Scan it again to review findings.",
        )

    finding = next((item for item in findings if item["id"] == finding_id), None)

    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    dismissed_ids = set(document.get("review", {}).get("dismissed_findings", []))

    if dismissed:
        dismissed_ids.add(finding_id)
        await save_finding_feedback(document, finding, current_user)
    else:
        dismissed_ids.discard(finding_id)
        await delete_finding_feedback(document_id, finding_id)

    scores = score_findings(findings, dismissed_ids)
    review = {
        "dismissed_findings": sorted(dismissed_ids),
        "effective_points": scores["effective_points"],
        "risk_score": scores["risk_score"],
        "trust_score": scores["trust_score"],
        "alert_level": scores["alert_level"],
    }

    await update_document_review(document_id, review)
    return {"review": review}


@router.post("/{document_id}/findings/{finding_id}/dismiss")
async def dismiss_finding(
    document_id: str,
    finding_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a finding as "not a risk": it stops counting towards the score."""
    return await set_finding_dismissed(document_id, finding_id, True, current_user)


@router.delete("/{document_id}/findings/{finding_id}/dismiss")
async def restore_finding(
    document_id: str,
    finding_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Undo "not a risk": the finding counts again."""
    return await set_finding_dismissed(document_id, finding_id, False, current_user)
