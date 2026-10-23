from app.ai.text_matching import find_phrase_positions

THREAT_PHRASES = {
    "pay or else": 35,
    "leak your data": 35,
    "release your information": 30,
    "blackmail": 35,
    "extortion": 35,
    "threaten": 25,
    "harm": 25,
    "legal action immediately": 20,
    "final warning": 20,

    # Gujarati threat phrases
    "પૈસા આપો નહીં તો": 35,
    "તમારો ડેટા લીક કરીશું": 35,
    "અંતિમ ચેતવણી": 20,
    "ધમકી": 25,
    "બ્લેકમેલ": 35,
}


def detect_threats(text: str) -> dict:
    threats = []
    total_risk_score = 0

    if not text:
        return {
            "threats_found": 0,
            "threat_risk_score": 0,
            "threats": [],
        }

    for phrase, risk_points in THREAT_PHRASES.items():
        positions = find_phrase_positions(text, phrase)

        for start_index, end_index in positions:
            threats.append(
                {
                    "phrase": phrase,
                    "risk_points": risk_points,
                    "start_index": start_index,
                    "end_index": end_index,
                }
            )

        # Repeating a phrase does not make the document more threatening.
        if positions:
            total_risk_score += risk_points

    total_risk_score = min(total_risk_score, 100)

    return {
        "threats_found": len(threats),
        "threat_risk_score": total_risk_score,
        "threats": threats,
    }
