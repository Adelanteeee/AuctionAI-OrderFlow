def visual_event(
    bear_failure, bull_failure, bear_watch, bull_watch,
    accepted_above, accepted_below, rejected_above, rejected_below,
    buying_absorption, selling_absorption,
    strong_bear_div, strong_bull_div,
):
    """Highest-priority visual state for RC9.4.2 Clean Visual."""
    if bear_failure:
        return "PF_DOWN"
    if bull_failure:
        return "PF_UP"
    if bear_watch:
        return "WATCH_DOWN"
    if bull_watch:
        return "WATCH_UP"
    if accepted_above:
        return "ACC_UP"
    if accepted_below:
        return "ACC_DOWN"
    if rejected_above:
        return "REJ_DOWN"
    if rejected_below:
        return "REJ_UP"
    if buying_absorption:
        return "BUY_ABS"
    if selling_absorption:
        return "SELL_ABS"
    if strong_bear_div:
        return "DIV_DOWN"
    if strong_bull_div:
        return "DIV_UP"
    return "NONE"
