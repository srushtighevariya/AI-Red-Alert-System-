def get_heatmap_color(risk_points: int) -> str:
    if risk_points >= 30:
        return "red"

    if risk_points >= 15:
        return "orange"

    return "yellow"


def get_heatmap_severity(risk_points: int) -> str:
    if risk_points >= 30:
        return "high"

    if risk_points >= 15:
        return "medium"

    return "low"


def add_highlights_from_items(
    highlights: list,
    category: str,
    label_key: str,
    items: list,
) -> None:
    for item in items:
        risk_points = item.get("risk_points", 0)

        highlights.append(
            {
                "category": category,
                "label": item.get(label_key, "Unknown"),
                "risk_points": risk_points,
                "severity": get_heatmap_severity(risk_points),
                "color": get_heatmap_color(risk_points),
                "start_index": item.get("start_index", 0),
                "end_index": item.get("end_index", 0),
            }
        )


def generate_document_heatmap(
    keyword_analysis: dict,
    sensitive_info_analysis: dict,
    policy_violation_analysis: dict,
    threat_analysis: dict,
) -> dict:
    highlights = []

    add_highlights_from_items(
        highlights=highlights,
        category="keyword",
        label_key="keyword",
        items=keyword_analysis.get("highlighted_sections", []),
    )

    add_highlights_from_items(
        highlights=highlights,
        category="sensitive_info",
        label_key="type",
        items=sensitive_info_analysis.get("findings", []),
    )

    add_highlights_from_items(
        highlights=highlights,
        category="policy_violation",
        label_key="phrase",
        items=policy_violation_analysis.get("violations", []),
    )

    add_highlights_from_items(
        highlights=highlights,
        category="threat",
        label_key="phrase",
        items=threat_analysis.get("threats", []),
    )

    return {
        "total_highlights": len(highlights),
        "highlights": highlights,
    }