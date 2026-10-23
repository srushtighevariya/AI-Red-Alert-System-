import pytest

from app.ai import pipeline
from app.ai.pipeline import analyze_document_text
from app.ai.redaction import mask_value, redact_text
from app.ai.summarizer import generate_basic_summary, split_into_sentences
from app.core.config import settings

CARD = "4111 1111 1111 1111"
AADHAAR = "2341 2341 2346"


# ── Masking ────────────────────────────────────────────────────────────


def test_mask_keeps_length():
    assert mask_value("4111111111111111") == "41************11"
    assert len(mask_value(CARD)) == len(CARD)


def test_redact_text_masks_only_the_spans():
    text = "Card 4111111111111111 ok"
    assert redact_text(text, [{"start_index": 5, "end_index": 21}]) == "Card 41************11 ok"


def test_stored_text_never_contains_raw_personal_data():
    text = (
        f"Confidential customer file. Card {CARD}. Aadhaar {AADHAAR}. "
        "Email priya@example.com, phone 9876543210."
    )
    analysis = analyze_document_text(text)
    stored = " ".join(
        [
            analysis["redacted_text"],
            analysis["summary"]["summary_text"],
            *analysis["summary"]["key_sentences"],
            *[section["excerpt"] for section in analysis["keyword_analysis"]["highlighted_sections"]],
        ]
    )

    for secret in [CARD, AADHAAR, "priya@example.com", "9876543210"]:
        assert secret not in stored


def test_highlight_positions_still_match_after_masking():
    text = f"Pay with card {CARD} — this is confidential."
    analysis = analyze_document_text(text)
    keyword = analysis["keyword_analysis"]["highlighted_sections"][0]
    assert analysis["redacted_text"][keyword["start_index"]:keyword["end_index"]] == "confidential"


# ── Summaries ──────────────────────────────────────────────────────────


def test_short_text_summary_is_the_text_itself():
    summary = generate_basic_summary("The team finished the backend. Testing starts next week.")
    assert summary["key_sentences"] == ["The team finished the backend.", "Testing starts next week."]


def test_summary_picks_central_sentences_not_just_the_first():
    text = (
        "Hello all. "
        "The vendor payment process changes next month. "
        "Payments to a vendor now need two approvals. "
        "The lunch menu has new items. "
        "Vendor payment approvals will be checked by finance. "
        "Finance will review every vendor payment approval weekly. "
        "Parking is closed on Friday. "
        "Questions about vendor payment approvals go to finance. "
        "The office party is on Saturday. "
        "Thanks."
    )
    summary = generate_basic_summary(text)
    assert len(summary["key_sentences"]) == 2  # 8 real sentences -> 2
    assert all("vendor" in sentence.lower() or "payment" in sentence.lower() for sentence in summary["key_sentences"])
    assert "Hello all." not in summary["key_sentences"]


def test_gujarati_sentences_are_split():
    assert len(split_into_sentences("આ દસ્તાવેજ ગોપનીય છે. પૈસા આપો નહીં તો ડેટા લીક કરીશું.")) == 2


def test_risk_summary_explains_the_findings():
    analysis = analyze_document_text("This is a final warning. Pay or else we will leak your data.")
    risk_summary = analysis["summary"]["risk_summary"]
    assert risk_summary.startswith("Red alert")
    assert '"pay or else"' in risk_summary


def test_risk_summary_for_a_clean_document():
    risk_summary = analyze_document_text("The team finished the sprint on time.")["summary"]["risk_summary"]
    assert "No threats, policy violations or personal data were found." in risk_summary


# ── AI model scoring rules (model replaced by a fake) ─────────────────


def fake_classify(signals):
    def classify(text):
        return {"status": "ok", "model": "fake", "reason": "", "signals": signals}

    return classify


def signal(key, confidence, points=30):
    return {"key": key, "label": key, "confidence": confidence, "evidence": "…", "points": points}


def test_confident_ai_signal_adds_points(monkeypatch):
    monkeypatch.setattr(pipeline, "classify", fake_classify([signal("policy", 0.95, points=25)]))
    analysis = analyze_document_text("Keep this payment out of the books so the auditors never find out.")
    assert analysis["semantic_analysis"]["semantic_risk_score"] == 24  # round(25 * 0.95)
    assert "AI model detected risky meaning" in analysis["risk_analysis"]["risk_factors"]


def test_unsure_ai_signal_is_ignored(monkeypatch):
    monkeypatch.setattr(pipeline, "classify", fake_classify([signal("fraud", settings.SEMANTIC_THRESHOLD - 0.01)]))
    analysis = analyze_document_text("Please process the invoice by Friday.")
    assert analysis["semantic_analysis"]["signals"] == []
    assert analysis["risk_analysis"]["risk_score"] == 0


def test_ai_signal_does_not_double_count_what_rules_found(monkeypatch):
    monkeypatch.setattr(pipeline, "classify", fake_classify([signal("threat", 0.99, points=35)]))
    analysis = analyze_document_text("This is a final warning. Pay or else we will leak your data.")
    [threat] = analysis["semantic_analysis"]["signals"]
    assert threat["already_found_by_rules"] and threat["points"] == 0


def test_app_works_when_model_is_unavailable():
    analysis = analyze_document_text("Pay or else.")
    assert analysis["semantic_analysis"]["status"] == "disabled"
    assert analysis["risk_analysis"]["alert_level"] in {"Yellow", "Red"}


def test_ai_alone_can_reach_yellow_but_never_red(monkeypatch):
    signals = [signal("threat", 0.99, 50), signal("fraud", 0.99, 45), signal("credentials", 0.99, 45)]
    monkeypatch.setattr(pipeline, "classify", fake_classify(signals))
    analysis = analyze_document_text("Do what we said by Friday, you know what happens otherwise.")
    assert analysis["risk_analysis"]["alert_level"] == "Yellow"
