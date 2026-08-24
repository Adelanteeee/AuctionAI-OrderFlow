import math
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


def test_absorption_event_is_transition_only(monkeypatch):
    import backtest.runner as runner_mod
    idx = pd.date_range('2026-01-01', periods=60, freq='1min', tz='UTC')
    p = pd.Series(100.0, index=idx)
    df = pd.DataFrame({'open':p,'high':p+.5,'low':p-.5,'close':p+.1,'volume':100.0}, index=idx)
    monkeypatch.setattr(runner_mod, 'absorption_score', lambda **kwargs: (80.0, 'SELLING ABSORBED', 'STRONG SELLING ABSORPTION'))
    events, _, _ = runner_mod.run_backtest(df, BacktestConfig(parent_timeframe='15min'), symbol='SYNTH')
    strong = events[events.event_type=='STRONG_SELLING_ABSORPTION']
    assert len(strong) == 1


def test_python_auction_reference_can_use_previous_session():
    idx = pd.date_range('2026-01-01', periods=3*24*60, freq='1min', tz='UTC')
    p = pd.Series(100.0, index=idx)
    for i, ts in enumerate(idx):
        local=ts.tz_convert('America/New_York')
        if local.date().isoformat()=='2026-01-02' and (local.hour*60+local.minute)>=570 and (local.hour*60+local.minute)<960:
            p.iloc[i]=120.0
    df=pd.DataFrame({'open':p,'high':p+.4,'low':p-.4,'close':p+.1,'volume':100.0},index=idx)
    cfg=BacktestConfig(parent_timeframe='15min',session_name='NewYork',auction_reference='PreviousSession')
    _,_,bars=run_backtest(df,cfg,symbol='SYNTH')
    jan3_session=bars[(bars.index.tz_convert('America/New_York').date.astype(str)=='2026-01-03') & bars.in_session]
    first=jan3_session.iloc[0]
    assert math.isclose(first.ref_poc, first.prev_session_poc, rel_tol=1e-9)
    assert not math.isclose(first.ref_poc, bars.loc[jan3_session.index[0], 'prev_day_poc'], rel_tol=1e-6)
