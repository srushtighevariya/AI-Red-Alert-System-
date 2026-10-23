def mask_value(value: str) -> str:
    """Keep the first and last two characters, star out the rest (same length)."""
    if len(value) <= 4:
        return "*" * len(value)

    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def redact_text(text: str, findings: list[dict]) -> str:
    """Mask every finding's span in the text.

    Masks keep the original length, so start/end indexes computed on the
    original text (highlights, heatmap) still point at the same place.
    """
    characters = list(text)

    for finding in findings:
        start, end = finding["start_index"], finding["end_index"]
        characters[start:end] = mask_value(text[start:end])

    return "".join(characters)
