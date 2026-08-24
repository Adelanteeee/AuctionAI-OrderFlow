def immediate_momentum(close, previous_close, atr, flat_atr_fraction=0.10):
    if atr is None or atr <= 0:
        return "FLAT"
    move = close - previous_close
    threshold = atr * flat_atr_fraction
    if move > threshold:
        return "UP"
    if move < -threshold:
        return "DOWN"
    return "FLAT"


def compact_context(
    delta_pct,
    cvd_bias,
    effort_result="",
    absorption="",
    event="",
    continuation="",
):
    sign = "+" if delta_pct > 0 else ""
    parts = [f"Δ {sign}{delta_pct:.0f}%"]
    parts.append(
        "CVD↑" if cvd_bias == "RISING" else "CVD↓" if cvd_bias == "FALLING" else "CVD→"
    )
    for part in (effort_result, absorption, event, continuation):
        if part:
            parts.append(part)
    return " | ".join(parts)
