import math
import pandas as pd
from backtest.config import BacktestConfig
from backtest.runner import run_backtest
from backtest.reporting import summarize_events


def test_session_volume_pace_uses_same_session_elapsed_time():
    idx = pd.date_range('2026-01-01 14:30', periods=2*24*60, freq='1min', tz='UTC')
    vol = pd.Series(0.0, index=idx)
    for ts in idx:
        local = ts.tz_convert('America/New_York')
        mins = local.hour*60+local.minute
        if 570 <= mins < 960:
            vol.loc[ts] = 100.0 if local.date().isoformat() == '2026-01-01' else 200.0
    p = pd.Series(100.0, index=idx)
    df = pd.DataFrame({'open':p,'high':p+.2,'low':p-.2,'close':p+.05,'volume':vol}, index=idx)
    cfg = BacktestConfig(parent_timeframe='15min', session_name='NewYork')
    _, _, bars = run_backtest(df, cfg, symbol='SYNTH')
    target = pd.Timestamp('2026-01-02 15:00', tz='UTC')
    assert math.isclose(float(bars.loc[target, 'session_volume_pace']), 200.0, rel_tol=1e-9)
    assert bars.loc[target, 'volume_pace_state'] == 'EXPANDING'


def test_summary_includes_context_groupings():
    ev = pd.DataFrame([
        {'event_type':'ACC_ABOVE_VAH','volume_pace_state':'EXPANDING','poc_migration':'POC RISING','value_migration':'VALUE SHIFTING UP','cvd_bias':'RISING','label':'VALID','dir_return_1':.1,'dir_return_3':.2,'dir_return_5':.3,'mfe_atr':.8,'mae_atr':.2},
        {'event_type':'ACC_ABOVE_VAH','volume_pace_state':'EXPANDING','poc_migration':'POC RISING','value_migration':'VALUE SHIFTING UP','cvd_bias':'RISING','label':'VALID','dir_return_1':.2,'dir_return_3':.3,'dir_return_5':.4,'mfe_atr':.9,'mae_atr':.1},
    ])
    s = summarize_events(ev, min_samples=1)
    assert {'group_type','group_value','event_type','sample_count'} <= set(s.columns)
    assert 'event+pace' in set(s.group_type)
    assert 'event+poc_migration' in set(s.group_type)
    assert 'event+value_migration' in set(s.group_type)
    assert 'event+cvd_bias' in set(s.group_type)
