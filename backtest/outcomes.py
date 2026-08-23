def evaluate_event(*, entry_close, atr, direction, future, threshold_atr=.5):
    if len(future)==0 or atr<=0:
        return {'label':'NEUTRAL','mfe_atr':0.0,'mae_atr':0.0}
    bullish = direction == 'bullish'
    mfe = mae = 0.0
    label = 'NEUTRAL'
    threshold = atr*threshold_atr
    for row in future.itertuples():
        fav = (row.high-entry_close) if bullish else (entry_close-row.low)
        adv = (entry_close-row.low) if bullish else (row.high-entry_close)
        mfe=max(mfe,fav); mae=max(mae,adv)
        if fav>=threshold and label=='NEUTRAL': label='VALID'; break
        if adv>=threshold and label=='NEUTRAL': label='FAILED'; break
    return {'label':label,'mfe_atr':mfe/atr,'mae_atr':mae/atr}
