import pandas as pd
from backtest.config import BacktestConfig
from backtest.divergence import confirmed_divergence_events
from backtest.reporting import summarize_events
from backtest.runner import run_backtest


def test_confirmed_bull_divergence_timestamps_confirmation_bar():
    idx = pd.date_range('2026-01-01', periods=9, freq='15min', tz='UTC')
    df = pd.DataFrame({'low':[10,9,8,9,10,9,7,9,10],'high':[11,10,9,10,11,10,8,10,11],'delta':[0,-1,-10,-2,0,-1,-5,-1,0],'cvd':[0,-1,-10,-8,-7,-8,-6,-5,-4]}, index=idx)
    ev = confirmed_divergence_events(df, left=1, right=1)
    bull = [e for e in ev if e['event_type']=='STRONG_BULL_DIVERGENCE']
    assert len(bull) == 1
    assert bull[0]['pivot_timestamp'] == idx[6]
    assert bull[0]['timestamp'] == idx[7]


def test_end_to_end_runner_returns_event_and_summary_frames():
    idx = pd.date_range('2026-01-01 00:00', periods=2*24*60, freq='1min', tz='UTC')
    base = pd.Series(range(len(idx)), index=idx, dtype=float)
    price = pd.Series(100.0, index=idx)
    price.iloc[24*60:] = 120.0 + (base.iloc[24*60:]-24*60)*0.002
    df = pd.DataFrame({'open':price,'high':price+0.4,'low':price-0.4,'close':price+0.1,'volume':100.0}, index=idx)
    cfg = BacktestConfig(parent_timeframe='15min', acceptance_closes=2, profile_rows=20)
    events, summary, bars = run_backtest(df, cfg, symbol='SYNTH')
    assert len(bars) > 100
    assert {'event_id','event_type','timestamp','auction_state','delta_pct','mfe_atr','mae_atr','label'} <= set(events.columns)
    assert len(events[events.event_type=='ACC_ABOVE_VAH']) >= 1
    assert len(summary) >= 1
    assert {'event_type','sample_count','valid_rate','avg_mfe_atr','avg_mae_atr'} <= set(summary.columns)


def test_summary_marks_low_samples():
    ev = pd.DataFrame([{'event_type':'X','label':'VALID','dir_return_1':.1,'dir_return_3':.2,'dir_return_5':.3,'mfe_atr':.7,'mae_atr':.2},{'event_type':'X','label':'FAILED','dir_return_1':-.1,'dir_return_3':-.2,'dir_return_5':-.3,'mfe_atr':.2,'mae_atr':.7}])
    s = summarize_events(ev, min_samples=5)
    assert s.iloc[0].sample_quality == 'LOW_SAMPLE'
