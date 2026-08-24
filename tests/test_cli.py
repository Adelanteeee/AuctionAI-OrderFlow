import pandas as pd
from backtest.cli import main


def test_cli_writes_events_and_summary(tmp_path):
    idx = pd.date_range('2026-01-01', periods=2*24*60, freq='1min', tz='UTC')
    p = pd.Series(100.0, index=idx)
    p.iloc[24*60:] = 120.0
    df = pd.DataFrame({'timestamp':idx.astype(str),'open':p.values,'high':p.values+.4,'low':p.values-.4,'close':p.values+.1,'volume':100.0})
    csv = tmp_path/'bars.csv'; out=tmp_path/'out'; df.to_csv(csv,index=False)
    rc = main(['--csv',str(csv),'--symbol','SYNTH','--timeframe','15min','--source-timezone','UTC','--output-dir',str(out)])
    assert rc == 0
    assert (out/'events.csv').exists()
    assert (out/'summary.csv').exists()
    assert (out/'bars.csv').exists()


def test_cli_accepts_previous_session_reference(tmp_path):
    idx = pd.date_range('2026-01-01', periods=2*24*60, freq='1min', tz='UTC')
    p = pd.Series(100.0, index=idx)
    df = pd.DataFrame({'timestamp':idx.astype(str),'open':p.values,'high':p.values+.4,'low':p.values-.4,'close':p.values+.1,'volume':100.0})
    csv=tmp_path/'bars.csv'; out=tmp_path/'out'; df.to_csv(csv,index=False)
    rc=main(['--csv',str(csv),'--symbol','SYNTH','--timeframe','15min','--source-timezone','UTC','--session','NewYork','--auction-reference','PreviousSession','--output-dir',str(out)])
    assert rc==0
