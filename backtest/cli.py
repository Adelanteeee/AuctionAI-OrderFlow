import argparse
from pathlib import Path
from .config import BacktestConfig
from .data import load_csv
from .runner import run_backtest


def build_parser():
    p=argparse.ArgumentParser(description='AuctionAI Order Flow event research backtester')
    p.add_argument('--csv',required=True)
    p.add_argument('--symbol',default='DATASET')
    p.add_argument('--timeframe',default='15min')
    p.add_argument('--source-timezone',default='UTC')
    p.add_argument('--session',default='NewYork',choices=['NewYork','London','Asia'])
    p.add_argument('--output-dir',required=True)
    return p


def main(argv=None):
    args=build_parser().parse_args(argv)
    df=load_csv(args.csv,args.source_timezone)
    cfg=BacktestConfig(parent_timeframe=args.timeframe, session_name=args.session)
    events,summary,bars=run_backtest(df,cfg,symbol=args.symbol)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/'events.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    bars.to_csv(out/'bars.csv',index_label='timestamp')
    print(f'Loaded {len(df)} 1m rows: {df.index.min()} -> {df.index.max()}')
    print(f'Parent bars: {len(bars)} | Events: {len(events)}')
    if not events.empty:
        print(events.event_type.value_counts().to_string())
    print(f'Wrote {out / "events.csv"}')
    print(f'Wrote {out / "summary.csv"}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
