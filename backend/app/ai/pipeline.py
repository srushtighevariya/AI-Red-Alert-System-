from app.ai.anomaly_detector import detect_abnormal_patterns
from app.ai.findings import MAX_SEMANTIC_POINTS, build_findings
from app.ai.heatmap_generator import generate_document_heatmap
from app.ai.indian_compliance_detector import detect_indian_compliance_data
from app.ai.keyword_detector import detect_risky_keywords
from app.ai.policy_violation_detector import detect_policy_violations
from app.ai.redaction import redact_text
from app.ai.risk_report_generator import generate_risk_report
from app.ai.risk_scoring import calculate_risk_result
from app.ai.semantic_classifier import classify
from app.ai.sensitive_info_detector import detect_sensitive_information
from app.ai.summarizer import generate_basic_summary, generate_risk_summary
from app.ai.tampering_detector import detect_tampering_suspicion
from app.ai.threat_detector import detect_threats
from app.core.config import settings

FRAUD_KEYWORDS = {"fraud", "fake", "urgent payment", "છેતરપિંડી", "નકલી", "તાત્કાલિક ચુકવણી"}
CREDENTIAL_KEYWORDS = {"password", "bank account", "પાસવર્ડ", "બેંક ખાતું"}

# MAX_SEMANTIC_POINTS (60): the model alone can make a document Yellow (needs
# review) but not Red; a Red alert always needs evidence from the rules too.

# The AI model only adds points for a category the rules did not already score,
# so the same risk is never counted twice.
RULE_COVERAGE = {
    "threat": lambda rules: rules["threat_analysis"]["threats_found"] > 0,
    "fraud": lambda rules: bool(FRAUD_KEYWORDS & set(rules["keyword_analysis"]["matched_keywords"])),
    "credentials": lambda rules: bool(CREDENTIAL_KEYWORDS & set(rules["keyword_analysis"]["matched_keywords"])),
    "policy": lambda rules: rules["policy_violation_analysis"]["policy_violations_found"] > 0,
}


def analyze_semantics(redacted_text: str, rule_results: dict) -> dict:
    result = classify(redacted_text)
    signals = []
    total_points = 0

    for signal in result["signals"]:
        if signal["confidence"] < settings.SEMANTIC_THRESHOLD:
            continue

        covered = RULE_COVERAGE[signal["key"]](rule_results)
        points = 0 if covered else round(signal["points"] * signal["confidence"])
        total_points += points

        signals.append(
            {
                **signal,
                "points": points,
                "counted": not covered,
                "already_found_by_rules": covered,
            }
        )

    return {
        "status": result["status"],
        "model": result["model"],
        "reason": result["reason"],
        "threshold": settings.SEMANTIC_THRESHOLD,
        "signals": signals,
        "semantic_risk_score": min(total_points, MAX_SEMANTIC_POINTS),
    }


def analyze_document_text(text: str) -> dict:
    sensitive_info_analysis = detect_sensitive_information(text)
    indian_compliance_analysis = detect_indian_compliance_data(
        text,
        exclude_spans=[
            (finding["start_index"], finding["end_index"])
            for finding in sensitive_info_analysis["findings"]
        ],
    )

    # Everything that is stored or shown (excerpts, summary, preview, AI
    # evidence) comes from this masked copy, never the raw text.
    redacted_text = redact_text(
        text,
        sensitive_info_analysis["findings"] + indian_compliance_analysis["findings"],
    )

    keyword_analysis = detect_risky_keywords(text, excerpt_text=redacted_text)
    policy_violation_analysis = detect_policy_violations(text)
    threat_analysis = detect_threats(text)
    anomaly_analysis = detect_abnormal_patterns(text)
    tampering_analysis = detect_tampering_suspicion(text)

    semantic_analysis = analyze_semantics(
        redacted_text,
        {
            "keyword_analysis": keyword_analysis,
            "threat_analysis": threat_analysis,
            "policy_violation_analysis": policy_violation_analysis,
        },
    )

    document_heatmap = generate_document_heatmap(
        keyword_analysis=keyword_analysis,
        sensitive_info_analysis=sensitive_info_analysis,
        policy_violation_analysis=policy_violation_analysis,
        threat_analysis=threat_analysis,
    )

    risk_result = calculate_risk_result(
        keyword_risk_score=keyword_analysis["keyword_risk_score"],
        sensitive_risk_score=sensitive_info_analysis["sensitive_risk_score"],
        policy_risk_score=policy_violation_analysis["policy_risk_score"],
        threat_risk_score=threat_analysis["threat_risk_score"],
        anomaly_risk_score=anomaly_analysis["anomaly_risk_score"],
        compliance_risk_score=indian_compliance_analysis["compliance_risk_score"],
        tampering_risk_score=tampering_analysis["tampering_risk_score"],
        semantic_risk_score=semantic_analysis["semantic_risk_score"],
    )

    risk_report = generate_risk_report(
        risk_analysis=risk_result,
        keyword_analysis=keyword_analysis,
        sensitive_info_analysis=sensitive_info_analysis,
        policy_violation_analysis=policy_violation_analysis,
        threat_analysis=threat_analysis,
        anomaly_analysis=anomaly_analysis,
        indian_compliance_analysis=indian_compliance_analysis,
        semantic_analysis=semantic_analysis,
    )

    analysis = {
        "keyword_analysis": keyword_analysis,
        "sensitive_info_analysis": sensitive_info_analysis,
        "policy_violation_analysis": policy_violation_analysis,
        "threat_analysis": threat_analysis,
        "risk_analysis": risk_result,
        "anomaly_analysis": anomaly_analysis,
        "risk_report": risk_report,
        "tampering_analysis": tampering_analysis,
        "indian_compliance_analysis": indian_compliance_analysis,
        "semantic_analysis": semantic_analysis,
        "document_heatmap": document_heatmap,
        "redacted_text": redacted_text,
    }

    analysis["findings"] = build_findings(analysis, redacted_text)

    summary = generate_basic_summary(redacted_text)
    summary["risk_summary"] = generate_risk_summary(analysis)
    analysis["summary"] = summary

    return analysis
