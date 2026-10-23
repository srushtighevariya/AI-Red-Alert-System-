import pytest

from app.ai.id_validators import is_valid_aadhaar, is_valid_luhn
from app.ai.indian_compliance_detector import detect_indian_compliance_data
from app.ai.keyword_detector import detect_risky_keywords
from app.ai.pipeline import analyze_document_text
from app.ai.sensitive_info_detector import detect_sensitive_information
from app.ai.tampering_detector import detect_tampering_suspicion
from app.ai.anomaly_detector import detect_abnormal_patterns
from app.ai.threat_detector import detect_threats


def alert_for(text: str) -> str:
    return analyze_document_text(text)["risk_analysis"]["alert_level"]


def finding_types(result: dict) -> list[str]:
    return [finding["type"] for finding in result["findings"]]


# ── Whole-word matching ────────────────────────────────────────────────


@pytest.mark.parametrize("text", ["The medicine is harmless.", "Visit the pharmacy.", "What a charming town."])
def test_threat_words_do_not_match_inside_other_words(text):
    assert detect_threats(text)["threats_found"] == 0


@pytest.mark.parametrize("text", ["He threatened us.", "They threaten staff.", "Nobody was harmed."])
def test_threat_words_match_english_inflections(text):
    assert detect_threats(text)["threats_found"] == 1


def test_multi_word_phrase_matches_across_line_breaks():
    assert detect_risky_keywords("Send it to my bank\naccount today.")["matched_keywords"] == ["bank account"]


def test_gujarati_phrase_matches_with_attached_suffix():
    assert detect_threats("આ ધમકીઓ ગંભીર છે.")["threats_found"] == 1


def test_gujarati_phrase_matches_when_ocr_drops_the_nasal_mark():
    assert detect_threats("પૈસા આપો નહી તો તમારો ડેટા લીક કરીશું.")["threats_found"] == 2


def test_repeated_phrase_is_scored_once():
    once = detect_threats("This is a final warning.")["threat_risk_score"]
    repeated = detect_threats("Final warning. Final warning. Final warning.")
    assert repeated["threat_risk_score"] == once
    assert repeated["threats_found"] == 3  # every occurrence is still highlighted


def test_single_word_is_not_scored_by_two_detectors():
    analysis = analyze_document_text("This movie is about blackmail.")
    assert analysis["keyword_analysis"]["keyword_risk_score"] == 0
    assert analysis["threat_analysis"]["threat_risk_score"] == 35


# ── ID numbers ─────────────────────────────────────────────────────────


def test_luhn():
    assert is_valid_luhn("4111 1111 1111 1111")
    assert not is_valid_luhn("4111 1111 1111 1112")


def test_aadhaar_checksum():
    assert is_valid_aadhaar("2341 2341 2346")
    assert not is_valid_aadhaar("2341 2341 2345")  # wrong check digit
    assert not is_valid_aadhaar("1341 2341 2346")  # cannot start with 1
    assert not is_valid_aadhaar("999999999999")  # placeholder, passes Verhoeff


def test_random_long_number_is_not_a_card():
    assert finding_types(detect_sensitive_information("Order number 1234567890123")) == []


def test_valid_card_is_detected_once():
    result = detect_sensitive_information("Card: 4111 1111 1111 1111")
    assert finding_types(result) == ["credit_card_number"]


def test_spaced_phone_number_is_detected():
    assert finding_types(detect_sensitive_information("Call +91 98765 43210")) == ["phone_number"]


def test_email_is_not_also_a_upi_id():
    text = "Write to support@shop.com today."
    assert finding_types(detect_sensitive_information(text)) == ["email_address"]
    assert finding_types(detect_indian_compliance_data(text)) == []


def test_upi_id_is_detected():
    assert finding_types(detect_indian_compliance_data("Pay ravi@okaxis.")) == ["upi_id"]


def test_number_needs_context_to_be_a_bank_account():
    assert finding_types(detect_indian_compliance_data("Order 123456789012 shipped.")) == []
    assert finding_types(detect_indian_compliance_data("Account no 123456789012")) == ["bank_account_number"]


def test_pan_inside_gstin_is_reported_once():
    assert finding_types(detect_indian_compliance_data("GSTIN 24ABCDE1234F1Z5")) == ["gstin"]


def test_phone_number_is_not_also_compliance_data():
    analysis = analyze_document_text("Contact the office on 9876543210 for details.")
    assert analysis["indian_compliance_analysis"]["compliance_items_found"] == 0
    assert analysis["sensitive_info_analysis"]["sensitive_items_found"] == 1


def test_repeated_personal_data_adds_a_little_per_item():
    one = detect_sensitive_information("a@x.com")["sensitive_risk_score"]
    three = detect_sensitive_information("a@x.com b@x.com c@x.com")["sensitive_risk_score"]
    assert three == one + 10


# ── Weak signals ───────────────────────────────────────────────────────


def test_plain_word_fraud_is_not_obfuscation():
    assert detect_tampering_suspicion("Possible fraud indicators.")["tampering_suspicions_found"] == 0
    assert detect_tampering_suspicion("Reset your p@ssw0rd now.")["tampering_suspicions_found"] == 1


def test_repeated_page_headers_are_not_tampering():
    text = "ACME Ltd\nPage 1\nResults were strong.\nACME Ltd\nPage 2"
    assert detect_tampering_suspicion(text)["tampering_suspicions_found"] == 0


def test_repeated_paragraph_is_tampering():
    line = "The payment must be sent to the new account before Friday."
    assert detect_tampering_suspicion(f"{line}\nOther text.\n{line}")["tampering_suspicions_found"] == 1


def test_faq_question_marks_are_not_an_anomaly():
    text = "How do I reset it? Where is my order? Can I return items? Is shipping free? What about refunds? Who do I call?"
    assert detect_abnormal_patterns(text)["anomalies_found"] == 0


def test_repeated_exclamation_marks_are_an_anomaly():
    types = [a["type"] for a in detect_abnormal_patterns("Pay now!!! This is important.")["anomalies"]]
    assert "excessive_warning_symbols" in types


# ── End-to-end alert levels ────────────────────────────────────────────


@pytest.mark.parametrize(
    "text",
    [
        "The pharmacy said the medicine is harmless. Please keep the password policy in mind.",
        "This project update describes weekly progress and the next sprint plan.",
        "ACME Ltd\nPage 1\nThe quarterly results were strong this year overall.\nACME Ltd\nPage 2",
    ],
)
def test_ordinary_documents_are_green(text):
    assert alert_for(text) == "Green"


def test_contact_details_are_yellow_not_red():
    assert alert_for("Contact us at support@shop.com or 9876543210 about order 1234567890123.") == "Yellow"


@pytest.mark.parametrize(
    "text",
    [
        "This is a final warning. Pay or else we will leak your data.",
        "Please bypass approval, ignore audit, and delete after reading.",
        "This file contains password information, fraud indicators, and bank account data.",
        "પૈસા આપો નહીં તો તમારો ડેટા લીક કરીશું. આ અંતિમ ચેતવણી છે.",
    ],
)
def test_clearly_risky_documents_are_red(text):
    assert alert_for(text) == "Red"
