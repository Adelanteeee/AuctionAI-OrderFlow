# AuctionAI Order Flow Python Event Backtest — Design Spec

## Goal

Build a Python backtest harness that reproduces the Universal Order Flow logic independently of TradingView so Auction, Absorption, Divergence, Delta/CVD, Daily Volume, Session Volume and Volume Profile events can be validated over hundreds of historical samples without Premium/Deep Backtesting.

A Pine RC9.1 bugfix is included only to make TradingView event markers transition-based and non-repeating; the Python harness is the primary validation system.

## Scope

### In scope

- Load 1-minute OHLCV data from CSV.
- Resample 1-minute data into configurable parent timeframes such as 5m, 15m and 30m.
- Reproduce the current Universal weighted intrabar Delta model.
- Reproduce CVD and CVD bias.
- Reproduce relative volume and Effort-vs-Result.
- Reproduce Daily Volume and Session Volume, including same-time pace versus the previous comparable period.
- Reproduce range-weighted Volume Profile with POC, VAH and VAL.
- Maintain Previous Day and Previous Session profile references separately from developing profiles.
- Reproduce Auction Acceptance/Rejection states against previous references.
- Reproduce Value Migration and POC Migration.
- Reproduce Absorption Score and state.
- Reproduce Delta/CVD divergence using confirmed pivots.
- Emit non-repeating event records for Acceptance, Rejection, Strong Absorption and Strong Divergence.
- Score event outcomes after 1, 3 and 5 parent bars.
- Calculate MFE and MAE for each event over the evaluation window.
- Export event-level CSV and aggregated summary CSV.
- RC9.1 Pine bugfix: event markers fire only on state transitions, not continuously while a state remains true.

### Out of scope for v1

- Broker/exchange API downloads.
- Live trading or live alerts.
- Position sizing, commissions, spread, slippage or PnL simulation.
- Automated parameter optimization.
- Machine learning.
- Footprint/Premium-only TradingView data.
- A full desktop/web UI.

## Input Data Contract

The harness accepts one or more CSV files containing 1-minute bars with at least:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

`timestamp` must be parseable by pandas. The CLI must accept a source timezone and normalize internally to timezone-aware timestamps.

Rows must be sorted by timestamp and duplicate timestamps must be rejected or deterministically de-duplicated with a clear warning.

## Core Architecture

The implementation is split into focused modules rather than one monolithic script.

```text
backtest/
  __init__.py
  config.py
  data.py
  delta.py
  volume.py
  profile.py
  auction.py
  absorption.py
  divergence.py
  events.py
  outcomes.py
  runner.py
  cli.py
  models.py
  reporting.py

tests/
  test_data.py
  test_delta.py
  test_volume.py
  test_profile.py
  test_auction.py
  test_absorption.py
  test_divergence.py
  test_events.py
  test_outcomes.py
  test_runner.py
```

Each module has one responsibility and exposes deterministic pure functions wherever possible.

## Configuration

A single dataclass owns model parameters so Pine and Python values can be kept aligned.

Defaults mirror RC9 unless otherwise noted:

- parent timeframe: `15min`
- lower timeframe: `1min`
- Delta body weight: `0.65`
- Delta close-location weight: `0.35`
- Intrabar pressure cap: `0.90`
- Strong Delta threshold: `20%`
- Minimum volume coverage: `70%`
- CVD smoothing: `5`
- Volume SMA length: `20`
- High volume multiplier: `1.5`
- Extreme volume multiplier: `2.5`
- Pace expanding threshold: `115%`
- Pace contracting threshold: `85%`
- ATR length: `14`
- High-result threshold: `0.5 ATR`
- Absorption minimum Delta: `20%`
- Pivot left/right: `3 / 3`
- Value Area: `70%`
- Profile rows: `28`
- Acceptance closes: `2`
- POC tolerance: `0.05 ATR`
- Rejection penetration: `0.03 ATR`
- Value shift threshold: `0.15` of previous value-area width

Session presets mirror Pine RC9:

- Asia: `09:00-18:00 Asia/Tokyo`
- London: `08:00-17:00 Europe/London`
- New York: `09:30-16:00 America/New_York`

Custom session and timezone are supported by configuration.

## Delta Model

For each 1-minute intrabar inside a parent bar:

1. `range = max(high - low, min_tick)`
2. `body_bias = clamp((close - open) / range, -1, 1)`
3. `close_bias = clamp(2 * (close - low) / range - 1, -1, 1)`
4. weighted pressure combines `body_bias` and `close_bias`
5. pressure is capped by `pressure_cap`
6. buy share = `0.5 + 0.5 * pressure`
7. sell share = `1 - buy_share`
8. estimated Delta = summed buy volume minus summed sell volume
9. Delta % = Delta / classified volume

The Python implementation must match the Pine formula exactly within floating-point tolerance.

## Parent-Bar Resampling

One-minute data is grouped into parent bars using timezone-aware timestamps and standard OHLCV aggregation:

- open = first
- high = max
- low = min
- close = last
- volume = sum

The original 1-minute rows remain attached logically to each parent bar so Delta and profile calculations use intrabars rather than reconstructed parent-only values.

## Volume Context

The harness computes:

- relative volume versus SMA
- high/extreme volume state
- current Daily Volume
- previous full Daily Volume
- Daily Volume Pace versus the same local clock minute of the previous day
- current Session Volume
- previous full Session Volume
- Session Volume Pace versus the same session clock minute of the previous session
- effective pace state: `EXPANDING`, `NORMAL`, `CONTRACTING`

When a same-time comparison is unavailable, pace is `NaN/N/A`; the system must not invent a comparison.

## Volume Profile

Profiles use the same range-weighted allocation principle as RC9:

- Determine profile low/high.
- Divide range into configurable rows.
- Allocate each 1-minute bar's volume across every row its high-low range overlaps, proportional to overlap.
- POC is the maximum-volume row.
- Value Area expands outward from POC until the configured percentage is included.

Maintain independently:

- developing day profile
- previous completed day profile
- developing selected session profile
- previous completed selected session profile

No future bars may contribute to a historical event's profile.

## Auction Engine

Auction states use the previous completed reference profile, never the developing profile.

Supported states:

- `TESTING ABOVE VAH`
- `ACCEPTED ABOVE VAH`
- `REJECTED ABOVE VAH`
- `TESTING BELOW VAL`
- `ACCEPTED BELOW VAL`
- `REJECTED BELOW VAL`
- `POC TEST`
- `ROTATION INSIDE VALUE`
- `ABOVE VAH`
- `BELOW VAL`
- `INSIDE VALUE`

Acceptance requires the configured number of consecutive confirmed parent closes beyond the previous VAH or VAL.

Rejection requires penetration beyond the reference boundary followed by a confirmed close back inside/through the boundary, consistent with RC9.

## Migration Engine

Developing profile is compared with previous reference profile to produce:

### Value Migration

- `VALUE SHIFTING UP`
- `VALUE SHIFTING DOWN`
- `VALUE OVERLAP`
- `VALUE DISPLACED`

### POC Migration

- `POC RISING`
- `POC FALLING`
- `POC STABLE`

These are context fields, not standalone trade signals in v1.

## Absorption Engine

Absorption score remains 0–100 and mirrors RC9 weighting:

- Delta strength: 30 points
- effort strength: 25 points
- low-result condition: 20 points
- rejection/close-location response: 25 points

Directional pressure is required before a directional absorption score is non-zero.

State thresholds:

- `<55`: no absorption
- `55–74.999`: possible absorption
- `>=75`: strong absorption

Event emission in the backtester uses Strong Absorption only by default, while all scores/states remain available in the event context.

## Divergence Engine

Use confirmed parent-bar pivots with configurable left/right widths.

Strong bullish divergence requires both:

- price lower low + Delta higher low
- price lower low + CVD higher low

Strong bearish divergence is symmetrical.

Only confirmed pivots are eligible, so event timestamps correspond to the confirmation bar while `pivot_timestamp` records the actual pivot bar.

## Event Model

Each emitted event receives a unique ID and must be non-repeating.

Primary event types:

- `ACC_ABOVE_VAH`
- `ACC_BELOW_VAL`
- `REJ_ABOVE_VAH`
- `REJ_BELOW_VAL`
- `STRONG_SELLING_ABSORPTION`
- `STRONG_BUYING_ABSORPTION`
- `STRONG_BULL_DIVERGENCE`
- `STRONG_BEAR_DIVERGENCE`

An Acceptance event fires only on the transition from not-accepted to accepted. It must not fire on every later bar that remains accepted. A new Acceptance is allowed only after the condition resets and becomes accepted again.

The same event-transition rule is applied to the RC9.1 Pine marker bugfix.

## Event Context Columns

Each event CSV row contains at least:

- event_id
- timestamp
- symbol/dataset name
- parent_timeframe
- event_type
- direction (`bullish`, `bearish`, `neutral` where relevant)
- close
- ATR
- Delta
- Delta %
- CVD
- CVD bias
- volume
- relative volume
- Daily Volume
- Daily Volume Pace
- Session Volume
- Session Volume Pace
- Volume Pace State
- reference type
- reference POC/VAH/VAL
- developing POC/VAH/VAL
- auction state
- auction confidence
- value migration
- POC migration
- absorption score
- absorption side/state
- pivot timestamp when relevant

## Outcome Measurement

The backtester evaluates event behavior, not trading PnL.

For each event, calculate at horizons of 1, 3 and 5 parent bars:

- forward close change in price units
- forward close change in ATR units
- directional forward return where bullish movement is positive for bullish events and bearish movement is positive for bearish events

For the first 5 parent bars after the event, calculate:

- MFE in price units
- MFE in ATR units
- MAE in price units
- MAE in ATR units

Default research validity labels:

- `VALID`: directional MFE reaches at least `0.5 ATR` within 5 bars before MAE reaches `0.5 ATR`
- `FAILED`: MAE reaches `0.5 ATR` before directional MFE reaches `0.5 ATR`
- `NEUTRAL`: neither threshold is reached within 5 bars

These thresholds are configuration values, not hard-coded assumptions.

## Aggregated Reports

Generate two CSV outputs:

### `events.csv`

One row per event with full context and outcomes.

### `summary.csv`

Group by at least:

- event type
- event type + Volume Pace State
- event type + POC Migration
- event type + Value Migration
- event type + CVD Bias

For each group report:

- sample count
- valid count/rate
- failed count/rate
- neutral count/rate
- average directional return at 1/3/5 bars
- median directional return at 1/3/5 bars
- average MFE ATR
- average MAE ATR

No group with fewer than a configurable minimum sample count should be presented as a reliable edge; it is still exported but marked `LOW_SAMPLE`.

## CLI

Example intended interface:

```bash
python -m backtest.cli \
  --csv data/BTCUSDT_1m.csv \
  --symbol BTCUSDT \
  --timeframe 15min \
  --source-timezone UTC \
  --session NewYork \
  --output-dir output/btc_15m
```

The CLI prints:

- loaded row count and date range
- parent bar count
- event count by event type
- output file paths
- any data-quality warnings

## RC9.1 Pine Bugfix

Create a new Pine file rather than overwriting RC9.

Expected behavior:

- Acceptance marker appears once when acceptance first becomes true.
- No repeated Acceptance markers while price remains accepted.
- Rejection marker appears only on the rejection event bar.
- Acceptance state can remain visible in HUD without repeated chart markers.
- After reset/re-entry and a later fresh acceptance, a new marker is allowed.
- No change to RC9 Delta, CVD, profile, migration or absorption formulas.

## Testing Strategy

Use pytest and TDD.

Unit tests must use tiny synthetic datasets with known expected outputs for:

- 1m -> parent resampling
- weighted Delta formula
- same-time Daily/Session pace
- profile POC/VAH/VAL
- previous-vs-developing profile separation
- acceptance transition firing once
- rejection event firing once
- migration states
- absorption thresholds
- confirmed divergence timing
- MFE/MAE and validity labeling

An integration test runs an end-to-end synthetic CSV through the runner and verifies deterministic `events.csv` and `summary.csv` contents.

## Verification Criteria

The subsystem is ready for research use when:

1. All pytest tests pass.
2. The integration fixture produces deterministic outputs.
3. Python weighted Delta matches hand-calculated synthetic examples.
4. Acceptance events are transition-based and non-repeating.
5. Historical event calculations are causal: no developing or previous profile uses future bars.
6. A user-supplied 1-minute CSV can be processed without TradingView or Premium features.
7. The implementation clearly labels the Universal Delta as an estimate, not true Bid/Ask footprint Delta.

## Deliverables

- `tradingview/AuctionAI_OrderFlow_v1_RC9_1.pine`
- Python `backtest/` package
- `tests/` suite
- sample config/usage documentation
- `events.csv` and `summary.csv` generation
- README section explaining how to run the research backtest
