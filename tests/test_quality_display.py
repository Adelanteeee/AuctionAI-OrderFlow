from backtest.quality import should_show_event


def test_default_hides_b_and_c():
    assert should_show_event("ACC_ABOVE_VAH", "B", show_only_a=True) is False
    assert should_show_event("ACC_BELOW_VAL", "A", show_only_a=True) is True


def test_divergence_never_labels_b_or_c():
    assert should_show_event("STRONG_BEAR_DIVERGENCE", "B", show_only_a=False) is False
    assert should_show_event("STRONG_BULL_DIVERGENCE", "C", show_only_a=False) is False


def test_divergence_labels_a_and_a_plus():
    assert should_show_event("STRONG_BEAR_DIVERGENCE", "A", show_only_a=True) is True
    assert should_show_event("STRONG_BEAR_DIVERGENCE", "A+", show_only_a=True) is True
