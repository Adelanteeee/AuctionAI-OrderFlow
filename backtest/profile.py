import math
import numpy as np

def profile_levels(highs, lows, vols, rows=28, value_area_pct=70.0):
    if len(vols) == 0:
        return math.nan, math.nan, math.nan
    p_lo, p_hi = float(min(lows)), float(max(highs))
    full_range = p_hi-p_lo
    if full_range <= 0:
        return p_lo, p_hi, p_lo
    row_size = full_range/rows
    buckets = np.zeros(rows, dtype=float)
    for ih, il, iv in zip(highs, lows, vols):
        ih, il, iv = float(ih), float(il), float(iv)
        intrabar_range = max(ih-il, 1e-12)
        start = max(0, min(rows-1, int(math.floor((il-p_lo)/row_size))))
        end = max(0, min(rows-1, int(math.floor((ih-p_lo)/row_size))))
        for r in range(start, end+1):
            row_lo = p_lo+r*row_size
            row_hi = row_lo+row_size
            overlap = max(0.0, min(ih,row_hi)-max(il,row_lo))
            if overlap > 0:
                buckets[r] += iv*overlap/intrabar_range
    total = float(buckets.sum())
    if total <= 0:
        return math.nan, math.nan, math.nan
    poc_idx = int(np.argmax(buckets))
    lo = hi = poc_idx
    va_v = float(buckets[poc_idx])
    target = total*value_area_pct/100.0
    while va_v < target and (lo>0 or hi<rows-1):
        lv = buckets[lo-1] if lo>0 else -1.0
        hv = buckets[hi+1] if hi<rows-1 else -1.0
        if hv >= lv and hi < rows-1:
            hi += 1; va_v += float(hv)
        elif lo > 0:
            lo -= 1; va_v += float(lv)
    poc = p_lo+(poc_idx+.5)*row_size
    val = p_lo+lo*row_size
    vah = p_lo+(hi+1)*row_size
    return poc, vah, val
