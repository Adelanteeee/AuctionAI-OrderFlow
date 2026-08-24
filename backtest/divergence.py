def confirmed_divergence_events(df, left=3, right=3):
    events=[]
    prev_low=None; prev_high=None
    n=len(df)
    for p in range(left, n-right):
        low=float(df.iloc[p].low); high=float(df.iloc[p].high)
        is_low=low < min(float(df.iloc[j].low) for j in range(p-left,p)) and low <= min(float(df.iloc[j].low) for j in range(p+1,p+right+1))
        is_high=high > max(float(df.iloc[j].high) for j in range(p-left,p)) and high >= max(float(df.iloc[j].high) for j in range(p+1,p+right+1))
        if is_low:
            cur=(low,float(df.iloc[p].delta),float(df.iloc[p].cvd),df.index[p])
            if prev_low and cur[0] < prev_low[0] and cur[1] > prev_low[1] and cur[2] > prev_low[2]:
                events.append({'event_type':'STRONG_BULL_DIVERGENCE','timestamp':df.index[p+right],'pivot_timestamp':df.index[p],'direction':'bullish'})
            prev_low=cur
        if is_high:
            cur=(high,float(df.iloc[p].delta),float(df.iloc[p].cvd),df.index[p])
            if prev_high and cur[0] > prev_high[0] and cur[1] < prev_high[1] and cur[2] < prev_high[2]:
                events.append({'event_type':'STRONG_BEAR_DIVERGENCE','timestamp':df.index[p+right],'pivot_timestamp':df.index[p],'direction':'bearish'})
            prev_high=cur
    return events
