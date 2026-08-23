import pandas as pd

METRIC_COLS=['dir_return_1','dir_return_3','dir_return_5','mfe_atr','mae_atr']

def _aggregate(g, min_samples, group_type, group_value, event_type):
    n=len(g); vc=g['label'].value_counts()
    return {
        'group_type':group_type,'group_value':group_value,'event_type':event_type,'sample_count':n,
        'valid_count':int(vc.get('VALID',0)),'valid_rate':float(vc.get('VALID',0)/n),
        'failed_count':int(vc.get('FAILED',0)),'failed_rate':float(vc.get('FAILED',0)/n),
        'neutral_count':int(vc.get('NEUTRAL',0)),'neutral_rate':float(vc.get('NEUTRAL',0)/n),
        'avg_dir_return_1':g['dir_return_1'].mean(),'avg_dir_return_3':g['dir_return_3'].mean(),'avg_dir_return_5':g['dir_return_5'].mean(),
        'median_dir_return_1':g['dir_return_1'].median(),'median_dir_return_3':g['dir_return_3'].median(),'median_dir_return_5':g['dir_return_5'].median(),
        'avg_mfe_atr':g['mfe_atr'].mean(),'avg_mae_atr':g['mae_atr'].mean(),
        'sample_quality':'OK' if n>=min_samples else 'LOW_SAMPLE'}

def summarize_events(events: pd.DataFrame, min_samples: int=10) -> pd.DataFrame:
    base_cols=['group_type','group_value','event_type','sample_count','valid_count','valid_rate','failed_count','failed_rate','neutral_count','neutral_rate','avg_dir_return_1','avg_dir_return_3','avg_dir_return_5','median_dir_return_1','median_dir_return_3','median_dir_return_5','avg_mfe_atr','avg_mae_atr','sample_quality']
    if events.empty:
        return pd.DataFrame(columns=base_cols)
    rows=[]
    for et,g in events.groupby('event_type',dropna=False):
        rows.append(_aggregate(g,min_samples,'event','ALL',et))
    contexts=[('event+pace','volume_pace_state'),('event+poc_migration','poc_migration'),('event+value_migration','value_migration'),('event+cvd_bias','cvd_bias')]
    for group_type,col in contexts:
        if col not in events.columns: continue
        for (et,val),g in events.groupby(['event_type',col],dropna=False):
            rows.append(_aggregate(g,min_samples,group_type,str(val),et))
    return pd.DataFrame(rows,columns=base_cols)
