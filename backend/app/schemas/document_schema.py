from pydantic import BaseModel


class SummaryResponse(BaseModel):
    summary_text: str
    key_sentences: list[str] = []
    risk_summary: str = ""
    word_count: int
    sentence_count: int


class SemanticSignalResponse(BaseModel):
    key: str
    label: str
    confidence: float
    evidence: str
    points: int
    counted: bool
    already_found_by_rules: bool
    start_index: int | None = None
    end_index: int | None = None


class FindingResponse(BaseModel):
    id: str
    category: str
    type: str
    label: str
    value: str
    base_points: int
    points: int
    start_index: int | None = None
    end_index: int | None = None
    line: int | None = None
    context: str = ""
    context_match_start: int | None = None
    context_match_end: int | None = None
    why: str
    what_to_do: str
    note: str = ""
    confidence: float | None = None


class SemanticAnalysisResponse(BaseModel):
    status: str
    model: str
    reason: str = ""
    threshold: float
    signals: list[SemanticSignalResponse]
    semantic_risk_score: int


class HighlightedSectionResponse(BaseModel):
    keyword: str
    risk_points: int
    start_index: int
    end_index: int
    excerpt: str


class KeywordAnalysisResponse(BaseModel):
    matched_keywords: list[str]
    keyword_count: int
    keyword_risk_score: int
    highlighted_sections: list[HighlightedSectionResponse]


class SensitiveFindingResponse(BaseModel):
    type: str
    masked_value: str
    risk_points: int
    start_index: int
    end_index: int


class SensitiveInfoAnalysisResponse(BaseModel):
    sensitive_items_found: int
    sensitive_risk_score: int
    findings: list[SensitiveFindingResponse]


class PolicyViolationItemResponse(BaseModel):
    phrase: str
    risk_points: int
    start_index: int
    end_index: int


class PolicyViolationAnalysisResponse(BaseModel):
    policy_violations_found: int
    policy_risk_score: int
    violations: list[PolicyViolationItemResponse]


class ThreatItemResponse(BaseModel):
    phrase: str
    risk_points: int
    start_index: int
    end_index: int


class ThreatAnalysisResponse(BaseModel):
    threats_found: int
    threat_risk_score: int
    threats: list[ThreatItemResponse]


class AnomalyItemResponse(BaseModel):
    type: str
    description: str
    risk_points: int


class AnomalyAnalysisResponse(BaseModel):
    anomalies_found: int
    anomaly_risk_score: int
    anomalies: list[AnomalyItemResponse]


class IndianComplianceFindingResponse(BaseModel):
    type: str
    masked_value: str
    risk_points: int
    start_index: int
    end_index: int


class IndianComplianceAnalysisResponse(BaseModel):
    compliance_items_found: int
    compliance_risk_score: int
    findings: list[IndianComplianceFindingResponse]


class TamperingFindingResponse(BaseModel):
    type: str
    description: str
    risk_points: int


class TamperingAnalysisResponse(BaseModel):
    tampering_suspicions_found: int
    tampering_risk_score: int
    findings: list[TamperingFindingResponse]


class RiskAnalysisResponse(BaseModel):
    risk_score: int
    trust_score: int
    alert_level: str
    risk_factors: list[str]


class RiskEvidenceItemResponse(BaseModel):
    category: str
    count: int
    explanation: str


class RiskReportResponse(BaseModel):
    title: str
    overview: str
    recommendation: str
    risk_score: int
    trust_score: int
    evidence: list[RiskEvidenceItemResponse]


class HeatmapHighlightResponse(BaseModel):
    category: str
    label: str
    risk_points: int
    severity: str
    color: str
    start_index: int
    end_index: int


class DocumentHeatmapResponse(BaseModel):
    total_highlights: int
    highlights: list[HeatmapHighlightResponse]


class DocumentUploadResponse(BaseModel):
    document_id: str
    message: str
    filename: str
    stored_filename: str
    uploaded_by: str
    uploaded_by_email: str
    text_extracted: bool
    character_count: int
    text_preview: str

    summary: SummaryResponse
    keyword_analysis: KeywordAnalysisResponse
    sensitive_info_analysis: SensitiveInfoAnalysisResponse
    policy_violation_analysis: PolicyViolationAnalysisResponse
    threat_analysis: ThreatAnalysisResponse
    anomaly_analysis: AnomalyAnalysisResponse
    indian_compliance_analysis: IndianComplianceAnalysisResponse
    tampering_analysis: TamperingAnalysisResponse
    risk_analysis: RiskAnalysisResponse
    risk_report: RiskReportResponse
    document_heatmap: DocumentHeatmapResponse
    semantic_analysis: SemanticAnalysisResponse | None = None
    findings: list[FindingResponse] = []
    document_text: str = ""
    document_text_truncated: bool = False


class DocumentHistoryItemResponse(BaseModel):
    document_id: str
    filename: str
    stored_filename: str
    uploaded_by: str | None = None
    uploaded_by_email: str | None = None
    risk_score: int
    alert_level: str
    created_at: str | None = None


class DocumentHistoryResponse(BaseModel):
    total: int
    documents: list[DocumentHistoryItemResponse]