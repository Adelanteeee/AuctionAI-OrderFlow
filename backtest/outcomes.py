def evaluate_event(*, entry_close, atr, direction, future, threshold_atr=.5):
    if len(future)==0 or atr<=0:
        return {'label':'NEUTRAL','mfe_atr':0.0,'mae_atr':0.0}
    bullish = direction == 'bullish'
    mfe = mae = 0.0
    label = 'NEUTRAL'
    decided = False
    threshold = atr*threshold_atr
    for row in future.itertuples():
        fav = (row.high-entry_close) if bullish else (entry_close-row.low)
        adv = (entry_close-row.low) if bullish else (row.high-entry_close)
        mfe=max(mfe,fav); mae=max(mae,adv)
        if not decided:
            hit_fav = fav >= threshold
            hit_adv = adv >= threshold
            if hit_fav and hit_adv:
                label='NEUTRAL'
                decided=True
            elif hit_fav:
                label='VALID'
                decided=True
            elif hit_adv:
                label='FAILED'
                decided=True
    return {'label':label,'mfe_atr':mfe/atr,'mae_atr':mae/atr}
