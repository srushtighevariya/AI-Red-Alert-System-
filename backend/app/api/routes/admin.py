from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_admin
from app.repositories.document_repository import get_all_documents

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/documents")
async def admin_document_history(
    limit: int = Query(50, ge=1, le=200),
    current_admin: dict = Depends(get_current_admin),
):
    documents = await get_all_documents(limit)

    return {
        "message": "Admin document history fetched successfully",
        "count": len(documents),
        "documents": documents,
    }