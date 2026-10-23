from fastapi import APIRouter

from app.repositories.analytics_repository import (
    get_alert_distribution,
    get_analytics_summary,
    get_recent_high_risk_documents,
)
from app.schemas.analytics_schema import (
    AlertDistributionItemResponse,
    AnalyticsSummaryResponse,
)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary():
    return await get_analytics_summary()

@router.get(
    "/alert-distribution",
    response_model=list[AlertDistributionItemResponse],
)
async def alert_distribution():
    return await get_alert_distribution()

@router.get("/recent-high-risk")
async def recent_high_risk_documents(limit: int = 5):
    documents = await get_recent_high_risk_documents(limit)

    return {
        "message": "Recent high-risk documents fetched successfully",
        "count": len(documents),
        "documents": documents,
    }