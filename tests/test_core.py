import math
import pandas as pd

from backtest.config import BacktestConfig
from backtest.data import resample_ohlcv
from backtest.delta import weighted_delta
from backtest.profile import profile_levels
from backtest.auction import AuctionTracker
from backtest.absorption import absorption_score
from backtest.outcomes import evaluate_event


def test_resample_1m_to_5m():
    idx = pd.date_range('2026-01-01 00:00', periods=5, freq='1min', tz='UTC')
    df = pd.DataFrame({'open':[1,2,3,4,5], 'high':[2,3,4,5,6], 'low':[0,1,2,3,4], 'close':[2,3,4,5,6], 'volume':[10,20,30,40,50]}, index=idx)
    out = resample_ohlcv(df, '5min')
    assert len(out) == 1
    row = out.iloc[0]
    assert row.open == 1 and row.high == 6 and row.low == 0 and row.close == 6 and row.volume == 150


def test_weighted_delta_matches_formula():
    bars = pd.DataFrame([{'open':10,'high':12,'low':9,'close':12,'volume':100},{'open':12,'high':13,'low':10,'close':10,'volume':80}])
    d, pct, classified = weighted_delta(bars, body_weight=.65, close_weight=.35, pressure_cap=.90, min_tick=.01)
    assert classified == 180
    assert math.isclose(d, 15.666666666666657, abs_tol=1e-9)
    assert math.isclose(pct, 8.703703703703699, abs_tol=1e-9)


def test_profile_levels_known_distribution():
    poc, vah, val = profile_levels([2.0,2.0,4.0],[0.0,0.0,2.0],[100.0,100.0,50.0],rows=4,value_area_pct=70)
    assert math.isclose(poc,0.5)
    assert math.isclose(val,0.0)
    assert math.isclose(vah,2.0)


def test_acceptance_fires_once_until_reset():
    t = AuctionTracker(acceptance_closes=2)
    e1=t.update(close=111,high=112,low=109,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    e2=t.update(close=112,high=113,low=111,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    e3=t.update(close=113,high=114,low=112,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    assert e1.event is None
    assert e2.event == 'ACC_ABOVE_VAH'
    assert e3.event is None
    assert e3.state == 'ACCEPTED ABOVE VAH'


def test_absorption_thresholds():
    score, side, state = absorption_score(delta_pct=-40,relative_volume=1.5,high_result=False,lower_wick_ratio=.5,upper_wick_ratio=.1,close_location=.8,min_delta_pct=20,high_vol_mult=1.5)
    assert score >= 75
    assert side == 'SELLING ABSORBED'
    assert state == 'STRONG SELLING ABSORPTION'


def test_outcome_valid_when_mfe_hits_first():
    future=pd.DataFrame([{'high':101.2,'low':99.8,'close':101.0},{'high':101.6,'low':100.4,'close':101.5},{'high':101.7,'low':100.8,'close':101.2},{'high':101.8,'low':100.9,'close':101.4},{'high':101.9,'low':101.0,'close':101.6}])
    out=evaluate_event(entry_close=100,atr=2,direction='bullish',future=future,threshold_atr=.5)
    assert out['label']=='VALID'
    assert out['mfe_atr']>=.5


def test_rejection_fires_once_until_boundary_rearmed():
    t = AuctionTracker(acceptance_closes=2, rejection_penetration_atr=.03)
    e1=t.update(close=109,high=111,low=108,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    e2=t.update(close=109,high=111,low=108,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    assert e1.event == 'REJ_ABOVE_VAH'
    assert e2.event is None
    t.update(close=111,high=112,low=110.5,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    e4=t.update(close=109,high=111,low=108,ref_poc=100,ref_vah=110,ref_val=90,atr=10)
    assert e4.event == 'REJ_ABOVE_VAH'


def test_outcome_keeps_full_horizon_mfe_mae_after_label_decision():
    future = pd.DataFrame([{'high':101.2,'low':99.8,'close':101.0},{'high':103.0,'low':98.0,'close':102.0},{'high':102.0,'low':99.0,'close':101.0}])
    out = evaluate_event(entry_close=100, atr=2, direction='bullish', future=future, threshold_atr=.5)
    assert out['label'] == 'VALID'
    assert math.isclose(out['mfe_atr'], 1.5)
    assert math.isclose(out['mae_atr'], 1.0)


def test_load_csv_warns_when_duplicate_timestamps_are_deduplicated(tmp_path):
    import warnings
    from backtest.data import load_csv
    p=tmp_path/'dup.csv'
    pd.DataFrame([{'timestamp':'2026-01-01 00:00:00','open':1,'high':2,'low':0,'close':1.5,'volume':10},{'timestamp':'2026-01-01 00:00:00','open':1,'high':3,'low':0,'close':2.0,'volume':20}]).to_csv(p,index=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        out=load_csv(str(p),'UTC')
    assert len(out)==1
    assert out.iloc[0].close==2.0
    assert any('duplicate timestamp' in str(w.message).lower() for w in caught)


def test_outcome_same_bar_both_thresholds_stays_neutral():
    future = pd.DataFrame([{'high':101.2,'low':98.8,'close':100.0},{'high':103.0,'low':99.5,'close':102.0}])
    out=evaluate_event(entry_close=100,atr=2,direction='bullish',future=future,threshold_atr=.5)
    assert out['label']=='NEUTRAL'
    assert math.isclose(out['mfe_atr'],1.5)
    assert math.isclose(out['mae_atr'],0.6)
