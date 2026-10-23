from app.ai.risk_scoring import calculate_risk_result, get_alert_level


def test_green_alert_level():
    assert get_alert_level(0) == "Green"
    assert get_alert_level(30) == "Green"


def test_yellow_alert_level():
    assert get_alert_level(31) == "Yellow"
    assert get_alert_level(70) == "Yellow"


def test_red_alert_level():
    assert get_alert_level(71) == "Red"
    assert get_alert_level(100) == "Red"


def test_risk_score_is_capped_at_100():
    result = calculate_risk_result(
        keyword_risk_score=90,
        sensitive_risk_score=35,
        policy_risk_score=55,
        threat_risk_score=100,
        anomaly_risk_score=25,
        compliance_risk_score=60,
        tampering_risk_score=50,
    )

    assert result["risk_score"] == 100
    assert result["alert_level"] == "Red"


def test_no_risk_is_green():
    result = calculate_risk_result(
        keyword_risk_score=0,
        sensitive_risk_score=0,
        policy_risk_score=0,
        threat_risk_score=0,
        anomaly_risk_score=0,
        compliance_risk_score=0,
        tampering_risk_score=0,
    )

    assert result["risk_score"] == 0
    assert result["alert_level"] == "Green"