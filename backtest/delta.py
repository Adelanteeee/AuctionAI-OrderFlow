import math
import pandas as pd

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def weighted_delta(intrabars: pd.DataFrame, body_weight=.65, close_weight=.35, pressure_cap=.90, min_tick=.01):
    buy = sell = classified = 0.0
    weight_sum = max(body_weight + close_weight, 0.0001)
    for row in intrabars.itertuples():
        r = max(float(row.high-row.low), min_tick)
        body_bias = _clamp((row.close-row.open)/r, -1.0, 1.0)
        close_bias = _clamp(((row.close-row.low)/r)*2.0-1.0, -1.0, 1.0)
        pressure_raw = (body_bias*body_weight + close_bias*close_weight)/weight_sum
        pressure = _clamp(pressure_raw, -pressure_cap, pressure_cap)
        buy_share = .5 + .5*pressure
        v = float(row.volume)
        buy += v*buy_share
        sell += v*(1.0-buy_share)
        classified += v
    delta = buy-sell
    pct = delta/classified*100.0 if classified > 0 else math.nan
    return delta, pct, classified
