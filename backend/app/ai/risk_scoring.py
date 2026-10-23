def get_alert_level(risk_score: int) -> str:
    if risk_score <= 30:
        return "Green"

    if risk_score <= 70:
        return "Yellow"

    return "Red"


def build_risk_factors(
    keyword_risk_score: int,
    sensitive_risk_score: int,
    policy_risk_score: int,
    threat_risk_score: int,
    anomaly_risk_score: int,
    compliance_risk_score: int = 0,
    tampering_risk_score: int = 0,
    semantic_risk_score: int = 0,
) -> list[str]:
    risk_factors = []

    if keyword_risk_score > 0:
        risk_factors.append("Risky keywords detected")

    if sensitive_risk_score > 0:
        risk_factors.append("Sensitive information detected")

    if policy_risk_score > 0:
        risk_factors.append("Policy violation indicators detected")

    if threat_risk_score > 0:
        risk_factors.append("Threat-related language detected")

    if anomaly_risk_score > 0:
        risk_factors.append("Abnormal text patterns detected")

    if compliance_risk_score > 0:
        risk_factors.append("Indian compliance data detected")

    if tampering_risk_score > 0:
        risk_factors.append("Possible text tampering detected")

    if semantic_risk_score > 0:
        risk_factors.append("AI model detected risky meaning")

    if not risk_factors:
        risk_factors.append("No major risk indicators detected")

    return risk_factors


def calculate_risk_result(
    keyword_risk_score: int,
    sensitive_risk_score: int = 0,
    policy_risk_score: int = 0,
    threat_risk_score: int = 0,
    anomaly_risk_score: int = 0,
    compliance_risk_score: int = 0,
    tampering_risk_score: int = 0,
    semantic_risk_score: int = 0,
) -> dict:
    risk_score = (
        keyword_risk_score
        + sensitive_risk_score
        + policy_risk_score
        + threat_risk_score
        + anomaly_risk_score
        + compliance_risk_score
        + tampering_risk_score
        + semantic_risk_score
    )
    risk_score = max(0, min(risk_score, 100))

    alert_level = get_alert_level(risk_score)
    trust_score = 100 - risk_score
    risk_factors = build_risk_factors(
        keyword_risk_score=keyword_risk_score,
        sensitive_risk_score=sensitive_risk_score,
        policy_risk_score=policy_risk_score,
        threat_risk_score=threat_risk_score,
        anomaly_risk_score=anomaly_risk_score,
        compliance_risk_score=compliance_risk_score,
        tampering_risk_score=tampering_risk_score,
        semantic_risk_score=semantic_risk_score,
    )

    return {
        "risk_score": risk_score,
        "trust_score": trust_score,
        "alert_level": alert_level,
        "risk_factors": risk_factors,
    }