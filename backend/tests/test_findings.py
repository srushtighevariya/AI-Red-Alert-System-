from app.ai.findings import score_findings
from app.ai.pipeline import analyze_document_text
from app.ai.sentences import split_sentences
from app.ai.summarizer import generate_basic_summary

NOTICE = (
    "Adv. R. K. Mehta\n"
    "E-Mail: counsel@example.com Mobile No.: 9876500001 & 9876500002\n"
    "This is a final warning. Pay or else we will leak your data. This is a final warning.\n"
)


def findings_by_category(analysis, category):
    return [finding for finding in analysis["findings"] if finding["category"] == category]


# ── Sentence splitting ─────────────────────────────────────────────────


def test_abbreviations_and_initials_do_not_end_sentences():
    text = "Adv. R. K. Mehta paid Rs. 2,000 on 5 Jan. 2026 for M/s. Aarav. He left."
    assert split_sentences(text) == [
        "Adv. R. K. Mehta paid Rs. 2,000 on 5 Jan. 2026 for M/s. Aarav.",
        "He left.",
    ]


def test_heading_lines_are_separate_but_wrapped_lines_are_joined():
    text = "LEGAL NOTICE\nThis long sentence was wrapped by the PDF in the middle of\nthe line and continues here."
    assert split_sentences(text) == [
        "LEGAL NOTICE",
        "This long sentence was wrapped by the PDF in the middle of the line and continues here.",
    ]


def test_summary_prefers_real_sentences_over_headers():
    text = (
        ":: H ::\nAdv. R. K. Mehta\nB.A., LL.B., ADVOCATE\n"
        "Subject: Legal notice for the cheque that was returned unpaid by your bank.\n"
        "My client supplied goods to you on credit and you issued the cheque as payment.\n"
        "The cheque was returned by the bank with the reason funds insufficient.\n"
    )
    for sentence in generate_basic_summary(text)["key_sentences"]:
        assert len(sentence.split()) >= 6


# ── Finding details ────────────────────────────────────────────────────


def test_every_located_finding_has_line_and_highlighted_context():
    analysis = analyze_document_text(NOTICE)

    for finding in analysis["findings"]:
        if finding["start_index"] is None:
            continue
        assert finding["line"] >= 1
        highlighted = finding["context"][finding["context_match_start"]:finding["context_match_end"]]
        assert highlighted == " ".join(analysis["redacted_text"][finding["start_index"]:finding["end_index"]].split())
        assert finding["why"] and finding["what_to_do"]


def test_findings_never_contain_raw_personal_data():
    analysis = analyze_document_text(NOTICE)
    text = str(analysis["findings"])
    assert "9876500001" not in text and "counsel@example.com" not in text


def test_finding_points_explain_repeats():
    analysis = analyze_document_text(NOTICE)
    phones = [f for f in findings_by_category(analysis, "sensitive") if f["type"] == "phone_number"]
    assert [phone["points"] for phone in phones] == [20, 5]

    warnings = [f for f in findings_by_category(analysis, "threat") if f["type"] == "final warning"]
    assert [warning["points"] for warning in warnings] == [20, 0]


# ── Scoring after "not a risk" ─────────────────────────────────────────


def test_score_from_findings_matches_the_pipeline():
    analysis = analyze_document_text(NOTICE)
    assert score_findings(analysis["findings"])["risk_score"] == analysis["risk_analysis"]["risk_score"]


def test_dismissing_the_first_repeat_promotes_the_next():
    analysis = analyze_document_text(NOTICE)
    first_phone = next(f for f in analysis["findings"] if f["type"] == "phone_number")
    second_phone = [f for f in analysis["findings"] if f["type"] == "phone_number"][1]

    scores = score_findings(analysis["findings"], {first_phone["id"]})
    assert scores["effective_points"][first_phone["id"]] == 0
    assert scores["effective_points"][second_phone["id"]] == 20


def test_a_phrase_stops_counting_only_when_every_occurrence_is_dismissed():
    analysis = analyze_document_text(NOTICE)
    warnings = [f["id"] for f in analysis["findings"] if f["type"] == "final warning"]
    full = score_findings(analysis["findings"])["category_scores"]["threat"]

    assert score_findings(analysis["findings"], {warnings[0]})["category_scores"]["threat"] == full
    assert score_findings(analysis["findings"], set(warnings))["category_scores"]["threat"] == full - 20


def test_dismissing_everything_gives_green():
    analysis = analyze_document_text(NOTICE)
    scores = score_findings(analysis["findings"], {f["id"] for f in analysis["findings"]})
    assert scores["risk_score"] == 0 and scores["alert_level"] == "Green"
