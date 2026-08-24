from backtest.continuation import trend_state, continuation_score, continuation_grade


def test_bearish_structure_requires_lower_high_and_lower_low():
    assert trend_state(prev_high=100, last_high=95, prev_low=90, last_low=85) == "BEARISH"


def test_bullish_structure_requires_higher_high_and_higher_low():
    assert trend_state(prev_high=100, last_high=105, prev_low=90, last_low=95) == "BULLISH"


def test_mixed_structure_is_neutral():
    assert trend_state(prev_high=100, last_high=105, prev_low=90, last_low=85) == "NEUTRAL"


def test_bearish_pullback_failure_scores_a_plus_when_evidence_stacks():
    score = continuation_score(
        trend="BEARISH",
        location_ok=True,
        absorption=True,
        high_effort_low_result=True,
        cvd_disagreement=True,
        confirmation=True,
    )
    assert score == 100
    assert continuation_grade(score) == "A+"


def test_watch_without_confirmation_stays_a():
    score = continuation_score(
        trend="BEARISH",
        location_ok=True,
        absorption=True,
        high_effort_low_result=False,
        cvd_disagreement=True,
        confirmation=False,
    )
    assert score == 75
    assert continuation_grade(score) == "A"


def test_no_trend_no_signal_score():
    assert continuation_score("NEUTRAL", True, True, True, True, True) == 0
