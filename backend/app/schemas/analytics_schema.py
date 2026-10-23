from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    total_documents: int = Field(ge=0)
    green_count: int = Field(ge=0)
    yellow_count: int = Field(ge=0)
    red_count: int = Field(ge=0)
    average_risk_score: float = Field(ge=0, le=100)

class AlertDistributionItemResponse(BaseModel):
    alert_level: str
    count: int = Field(ge=0)