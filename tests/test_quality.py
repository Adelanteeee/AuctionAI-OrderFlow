from backtest.quality import quality_score, quality_grade


def test_acc_above_expanding_is_a_plus():
    score = quality_score("ACC_ABOVE_VAH", "EXPANDING", "RISING")
    assert score == 90
    assert quality_grade(score) == "A+"


def test_acc_below_contracting_is_a():
    score = quality_score("ACC_BELOW_VAL", "CONTRACTING", "FALLING")
    assert score == 80
    assert quality_grade(score) == "A"


def test_bear_div_contracting_falling_is_a_plus():
    score = quality_score("STRONG_BEAR_DIVERGENCE", "CONTRACTING", "FALLING")
    assert score == 90
    assert quality_grade(score) == "A+"


def test_bull_div_stays_low_without_evidence():
    score = quality_score("STRONG_BULL_DIVERGENCE", "NORMAL", "RISING")
    assert score == 45
    assert quality_grade(score) == "C"


def test_structure_qualified_buying_absorption_is_b():
    score = quality_score("STRONG_BUYING_ABSORPTION", "NORMAL", "RISING")
    assert score == 70
    assert quality_grade(score) == "B"


def test_unknown_event_is_zero_and_c():
    score = quality_score("UNKNOWN", "NORMAL", "FLAT")
    assert score == 0
    assert quality_grade(score) == "C"
