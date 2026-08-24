# AuctionAI Order Flow — Python Event Backtest

This research harness validates the **Universal estimated Delta** edition without TradingView Premium. It does **not** use true Bid/Ask footprint data and it is not a PnL strategy tester.

## Input CSV

Required columns:

```text
timestamp,open,high,low,close,volume
```

Use one-minute bars. Timestamps may already contain a timezone; otherwise pass the source timezone on the CLI.

## Run

```bash
python -m backtest.cli \
  --csv data/XAUUSD_1m.csv \
  --symbol XAUUSD \
  --timeframe 15min \
  --source-timezone UTC \
  --session NewYork \
  --auction-reference PreviousDay \
  --output-dir output/xauusd_15m
```

Auction reference choices are `PreviousDay` and `PreviousSession`.

Outputs:

- `events.csv`: one row per non-repeating research event with context, 1/3/5-bar directional returns, MFE/MAE and VALID/FAILED/NEUTRAL label.
- `summary.csv`: aggregate statistics by event type and context combinations (pace, POC migration, value migration, CVD bias). Groups below 10 samples are labeled `LOW_SAMPLE`.
- `bars.csv`: enriched parent-bar dataset for debugging and parity checks.

## Event validity

Default research label over the next five parent bars:

- `VALID`: directional MFE reaches +0.5 ATR before adverse excursion reaches 0.5 ATR.
- `FAILED`: adverse excursion reaches 0.5 ATR first.
- `NEUTRAL`: neither threshold is reached.

MFE and MAE themselves are measured across the full five-bar evaluation window, even after the validity label is determined.

This is an event-quality test, not an entry/SL/TP trading rule.

## Test

```bash
python -m pytest -q
```
