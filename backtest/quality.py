BASE_SCORES = {
    "ACC_ABOVE_VAH": 60,
    "ACC_BELOW_VAL": 60,
    "REJ_ABOVE_VAH": 45,
    "REJ_BELOW_VAL": 45,
    "STRONG_BEAR_DIVERGENCE": 60,
    "STRONG_BULL_DIVERGENCE": 45,
    "STRONG_BUYING_ABSORPTION": 70,
    "STRONG_SELLING_ABSORPTION": 60,
}


def quality_score(event_type: str, pace_state: str, cvd_bias: str) -> int:
    """Experimental research ranking, not a win probability."""
    score = BASE_SCORES.get(event_type, 0)

    if event_type == "ACC_ABOVE_VAH":
        if pace_state == "EXPANDING":
            score += 30
        elif pace_state == "CONTRACTING":
            score += 15
    elif event_type == "ACC_BELOW_VAL":
        if pace_state == "CONTRACTING":
            score += 20
        elif pace_state == "EXPANDING":
            score += 10
    elif event_type == "STRONG_BEAR_DIVERGENCE":
        if pace_state == "CONTRACTING":
            score += 20
        if cvd_bias == "FALLING":
            score += 10

    return max(0, min(100, int(score)))


def quality_grade(score: int) -> str:
    if score >= 85:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    return "C"


def should_show_event(event_type: str, grade: str, show_only_a: bool = True) -> bool:
    """RC9.3.1 visual filter: default A/A+, and divergences never label below A."""
    high_grade = grade in {"A", "A+"}
    if event_type in {"STRONG_BEAR_DIVERGENCE", "STRONG_BULL_DIVERGENCE"}:
        return high_grade
    return high_grade if show_only_a else True
