def generate_risk_report(
    risk_analysis: dict,
    keyword_analysis: dict,
    sensitive_info_analysis: dict,
    policy_violation_analysis: dict,
    threat_analysis: dict,
    anomaly_analysis: dict,
    indian_compliance_analysis: dict,
    semantic_analysis: dict | None = None,
) -> dict:
    risk_score = risk_analysis["risk_score"]
    alert_level = risk_analysis["alert_level"]

    if alert_level == "Red":
        overview = "This document contains serious risk indicators."
        recommendation = "Do not share or approve this document before manual review."
    elif alert_level == "Yellow":
        overview = "This document contains moderate risk indicators."
        recommendation = "Review the detected evidence before using or sharing this document."
    else:
        overview = "No major risk indicators were detected."
        recommendation = "The document appears low-risk, but normal verification is still recommended."

    evidence = []

    categories = [
        ("Risky keywords", keyword_analysis["keyword_count"]),
        ("Sensitive information", sensitive_info_analysis["sensitive_items_found"]),
        ("Policy violations", policy_violation_analysis["policy_violations_found"]),
        ("Threat indicators", threat_analysis["threats_found"]),
        ("Abnormal patterns", anomaly_analysis["anomalies_found"]),
        (
            "Indian compliance data",
            indian_compliance_analysis["compliance_items_found"],
        ),
        (
            "AI model signals",
            sum(1 for signal in (semantic_analysis or {}).get("signals", []) if signal["counted"]),
        ),
    ]

    for category, count in categories:
        if count > 0:
            evidence.append(
                {
                    "category": category,
                    "count": count,
                    "explanation": f"{count} {category.lower()} item(s) detected.",
                }
            )

    return {
        "title": f"{alert_level} Alert Risk Report",
        "overview": overview,
        "recommendation": recommendation,
        "risk_score": risk_score,
        "trust_score": risk_analysis["trust_score"],
        "evidence": evidence,
    }