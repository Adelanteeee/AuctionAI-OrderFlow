def trend_state(prev_high, last_high, prev_low, last_low):
    """Return confirmed swing-structure trend state."""
    if None in (prev_high, last_high, prev_low, last_low):
        return "NEUTRAL"
    if last_high < prev_high and last_low < prev_low:
        return "BEARISH"
    if last_high > prev_high and last_low > prev_low:
        return "BULLISH"
    return "NEUTRAL"


def continuation_score(
    trend,
    location_ok,
    absorption,
    high_effort_low_result,
    cvd_disagreement,
    confirmation,
):
    """Research score for pullback-failure / trend-continuation evidence."""
    if trend not in {"BEARISH", "BULLISH"}:
        return 0

    score = 25
    if location_ok:
        score += 20
    if absorption:
        score += 20
    if high_effort_low_result:
        score += 15
    if cvd_disagreement:
        score += 10
    if confirmation:
        score += 10
    return min(100, score)


def continuation_grade(score):
    if score >= 90:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    return "C"
