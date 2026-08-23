# Python Event Backtest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python event-validation backtester that reproduces AuctionAI Order Flow Universal logic from 1-minute OHLCV and fixes RC9 Pine event markers so Acceptance/Rejection markers fire only on transitions.

**Architecture:** Keep Pine and Python behavior aligned through shared documented formulas, but implement the Python harness as a deterministic research package with pure functions and synthetic test fixtures. Data flows from 1-minute CSV → validated/resampled parent bars → Delta/volume/profile/context engines → event detector → forward-outcome scorer → CSV reports. RC9.1 remains a separate Pine file and changes only event emission, not RC9 calculation formulas.

**Tech Stack:** Python 3.11+, pandas, numpy, pytest, standard-library dataclasses/argparse/pathlib/zoneinfo, Pine Script v6.

**Spec:** `docs/superpowers/specs/2026-08-23-python-event-backtest-design.md`

## Global Constraints

- Do not modify `Adelanteeee/AuctionAI`.
- Work only in `Adelanteeee/AuctionAI-OrderFlow` on `feature/order-flow-v1`.
- Preserve `tradingview/AuctionAI_OrderFlow_v1_RC9.pine`; create RC9.1 separately.
- Python Delta must be explicitly labeled an estimated Universal Delta, not true Bid/Ask footprint Delta.
- No broker API, live trading, machine learning, optimizer, or UI in v1.
- All historical calculations must be causal; future bars must never influence an event.
- Use pytest and TDD for Python changes.
- Default parent timeframe is `15min`; lower timeframe is 1 minute.
- Default profile rows `28`; Value Area `70%`; acceptance closes `2`.

---

### Task 1: Project skeleton and configuration contract

**Files:**
- Create: `backtest/__init__.py`
- Create: `backtest/config.py`
- Create: `backtest/models.py`
- Create: `tests/test_config.py`
- Create: `requirements-backtest.txt`

**Interfaces:**
- Produces: `BacktestConfig` dataclass and shared typed result containers used by later tasks.

- [ ] **Step 1: Write failing configuration tests**

Create `tests/test_config.py` with tests asserting defaults:

```python
from backtest.config import BacktestConfig


def test_backtest_config_defaults_match_rc9():
    cfg = BacktestConfig()
    assert cfg.parent_timeframe == "15min"
    assert cfg.delta_body_weight == 0.65
    assert cfg.delta_close_weight == 0.35
    assert cfg.delta_pressure_cap == 0.90
    assert cfg.min_volume_coverage == 0.70
    assert cfg.profile_rows == 28
    assert cfg.value_area_pct == 70.0
    assert cfg.acceptance_closes == 2
    assert cfg.validity_threshold_atr == 0.5
    assert cfg.outcome_horizon_bars == 5
```

- [ ] **Step 2: Run test and confirm expected failure**

Run:

```bash
pytest tests/test_config.py -v
```

Expected: FAIL because `backtest.config` does not exist.

- [ ] **Step 3: Implement minimal config/models**

Create `BacktestConfig` with explicit defaults from the design spec and create typed dataclasses in `models.py` for `ProfileLevels`, `EventRecord`, and `OutcomeResult`.

- [ ] **Step 4: Add dependency file**

`requirements-backtest.txt`:

```text
pandas>=2.2,<3
numpy>=2.0,<3
pytest>=8,<9
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message:

```text
feat: add backtest configuration foundation
```

---

### Task 2: CSV validation and parent-bar resampling

**Files:**
- Create: `backtest/data.py`
- Create: `tests/test_data.py`

**Interfaces:**
- Consumes: `BacktestConfig`.
- Produces: `load_1m_csv(path, source_timezone) -> DataFrame` and `resample_parent_bars(df, timeframe) -> DataFrame`.

- [ ] **Step 1: Write failing data tests**

Use a six-row synthetic 1-minute DataFrame. Assert:

- columns are normalized to lowercase required fields
- timestamps become timezone-aware
- rows sort ascending
- duplicate timestamps raise `ValueError`
- 1m→5m aggregation yields first open, max high, min low, last close, summed volume

Example expected first 5m bar:

```python
assert row.open == 100.0
assert row.high == 106.0
assert row.low == 99.0
assert row.close == 105.0
assert row.volume == 150.0
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_data.py -v
```

Expected: FAIL because functions are missing.

- [ ] **Step 3: Implement loader and resampler**

Require columns `timestamp/open/high/low/close/volume`; parse timestamp with pandas; localize naive timestamps to user-specified timezone; convert to UTC internally; reject duplicates; resample with `label="left", closed="left"`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```text
feat: add csv validation and bar resampling
```

---

### Task 3: Weighted Universal Delta engine

**Files:**
- Create: `backtest/delta.py`
- Create: `tests/test_delta.py`

**Interfaces:**
- Produces: `estimate_intrabar_delta(intrabars, cfg) -> dict[str, float]` returning buy volume, sell volume, Delta, Delta %, classified volume, and volume coverage.

- [ ] **Step 1: Write hand-calculated failing tests**

Construct one bullish and one bearish intrabar with known OHLCV. Compute expected pressure using exactly:

```python
range_ = max(high - low, min_tick)
body_bias = clip((close - open) / range_, -1, 1)
close_bias = clip(((close - low) / range_) * 2 - 1, -1, 1)
pressure_raw = (
    body_bias * cfg.delta_body_weight
    + close_bias * cfg.delta_close_weight
) / (cfg.delta_body_weight + cfg.delta_close_weight)
pressure = clip(pressure_raw, -cfg.delta_pressure_cap, cfg.delta_pressure_cap)
buy_share = 0.5 + 0.5 * pressure
```

Assert Python result matches the manual result within `1e-9`.

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_delta.py -v
```

- [ ] **Step 3: Implement minimal Delta engine**

Use numpy clipping, preserve float precision, and explicitly name output as estimated Delta in docstrings.

- [ ] **Step 4: Add coverage test**

Assert `classified_volume / parent_volume` is capped at `1.0`.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_delta.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```text
feat: reproduce weighted universal delta
```

---

### Task 4: Volume, ATR, CVD, and same-time pace

**Files:**
- Create: `backtest/volume.py`
- Create: `tests/test_volume.py`

**Interfaces:**
- Produces: `add_volume_context(parent_df, cfg, session_name) -> DataFrame`.
- Adds ATR, relative volume, daily/session cumulative volume, daily/session same-time pace, volume pace state, CVD, smoothed CVD, and CVD bias.

- [ ] **Step 1: Write failing ATR/relative-volume test**

Use a deterministic series and assert SMA-relative volume and ATR values at known rows.

- [ ] **Step 2: Write failing same-time Daily Pace test**

Create two synthetic days with identical bar times and day-two cumulative volume exactly double day one. Assert day-two pace at the matching local minute is `200.0`.

- [ ] **Step 3: Write failing Session Pace test**

Create two New York session fixtures. Assert the second session's cumulative volume at the same session time compares against the first session and yields the expected percentage.

- [ ] **Step 4: Run tests and confirm failure**

```bash
pytest tests/test_volume.py -v
```

- [ ] **Step 5: Implement volume context**

Use timezone-aware session masks with `zoneinfo.ZoneInfo`; prefer Session Pace when the active session pace is available, otherwise Daily Pace; map pace to `EXPANDING/NORMAL/CONTRACTING` using config thresholds.

- [ ] **Step 6: Implement CVD context**

CVD is cumulative estimated Delta; EMA smoothing period is config-driven; bias is `RISING/FALLING/FLAT` based on smoothed slope.

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_volume.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```text
feat: add volume pace atr and cvd context
```

---

### Task 5: Range-weighted Volume Profile and reference separation

**Files:**
- Create: `backtest/profile.py`
- Create: `tests/test_profile.py`

**Interfaces:**
- Produces: `calculate_profile(intrabars, rows, value_area_pct, min_tick) -> ProfileLevels`.
- Produces: `add_profile_context(parent_df, intrabars_by_parent, cfg, session) -> DataFrame` with previous/developing day and session POC/VAH/VAL.

- [ ] **Step 1: Write failing profile allocation test**

Use a small synthetic profile where volume is concentrated in a known middle row. Assert POC lands on that row center and VAH/VAL bracket the configured 70% volume.

- [ ] **Step 2: Write failing causality test**

Build day 1 and day 2. Assert the first bar of day 2 sees day 1 as `previous_day_*`, while developing day 2 levels do not contain any later day-2 intrabars.

- [ ] **Step 3: Write failing session-reference test**

Create two sessions and assert previous-session profile switches only on the next session start.

- [ ] **Step 4: Run failing tests**

```bash
pytest tests/test_profile.py -v
```

- [ ] **Step 5: Implement profile calculator**

Allocate each intrabar's volume proportionally to every price row overlapped by its high-low range. Expand value area outward from POC, choosing the larger adjacent row first.

- [ ] **Step 6: Implement causal day/session state machine**

Snapshot completed profile on reset; then clear developing storage; update developing profile only with bars available up to current event time.

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_profile.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```text
feat: add causal previous and developing profiles
```

---

### Task 6: Auction states and migration engine

**Files:**
- Create: `backtest/auction.py`
- Create: `tests/test_auction.py`

**Interfaces:**
- Produces: `add_auction_context(df, cfg, reference_type) -> DataFrame`.
- Adds auction state, auction confidence, value migration, and POC migration.

- [ ] **Step 1: Write failing Acceptance transition tests**

Given previous VAH=100 and closes `[99, 101, 102, 103]` with `acceptance_closes=2`, assert:

- bar 101: not accepted
- bar 102: `ACCEPTED ABOVE VAH`
- bar 103: state may remain accepted but `acceptance_event=False`

- [ ] **Step 2: Write failing Rejection tests**

For previous VAH=100, high=101 and close=99.5 with sufficient ATR penetration, assert `REJECTED ABOVE VAH` and `rejection_event=True` only on that bar.

- [ ] **Step 3: Write failing migration tests**

Assert known previous/developing centers map to `VALUE SHIFTING UP`, `VALUE SHIFTING DOWN`, `VALUE OVERLAP`, and known POC offsets map to `POC RISING/FALLING/STABLE`.

- [ ] **Step 4: Run failing tests**

```bash
pytest tests/test_auction.py -v
```

- [ ] **Step 5: Implement auction state machine**

Maintain consecutive close counts, event booleans that fire only at threshold crossing, rejection booleans that fire only on event bars, and RC9 confidence formula.

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_auction.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```text
feat: add auction state and migration engine
```

---

### Task 7: Absorption engine

**Files:**
- Create: `backtest/absorption.py`
- Create: `tests/test_absorption.py`

**Interfaces:**
- Produces: `add_absorption_context(df, cfg) -> DataFrame`.

- [ ] **Step 1: Write failing threshold tests**

Construct rows that produce scores just below 55, between 55 and 75, and at/above 75. Assert states:

```text
NO ABSORPTION
POSSIBLE ... ABSORPTION
STRONG ... ABSORPTION
```

- [ ] **Step 2: Write directional naming test**

Negative Delta with lower rejection must label `SELLING ABSORBED`; positive Delta with upper rejection must label `BUYING ABSORBED`.

- [ ] **Step 3: Run failing tests**

```bash
pytest tests/test_absorption.py -v
```

- [ ] **Step 4: Implement RC9 score formula exactly**

Weights: 30 Delta + 25 effort + 20 low result + 25 rejection/close-location.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_absorption.py -v
```

- [ ] **Step 6: Commit**

```text
feat: add absorption scoring engine
```

---

### Task 8: Confirmed divergence engine

**Files:**
- Create: `backtest/divergence.py`
- Create: `tests/test_divergence.py`

**Interfaces:**
- Produces: `add_divergence_context(df, cfg) -> DataFrame`.

- [ ] **Step 1: Write failing bullish divergence test**

Create two confirmed price pivot lows where the second price low is lower but Delta and CVD pivots are higher. Assert a strong bullish divergence event appears only `pivot_right` bars after the actual pivot and records `pivot_timestamp`.

- [ ] **Step 2: Write symmetric bearish test**

- [ ] **Step 3: Run failing tests**

```bash
pytest tests/test_divergence.py -v
```

- [ ] **Step 4: Implement confirmed pivot detector**

A pivot at index `i` is known only after `pivot_right` later bars exist. Never mark divergence before confirmation.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_divergence.py -v
```

- [ ] **Step 6: Commit**

```text
feat: add confirmed delta cvd divergence
```

---

### Task 9: Event emission and deduplication

**Files:**
- Create: `backtest/events.py`
- Create: `tests/test_events.py`

**Interfaces:**
- Produces: `extract_events(df, symbol, timeframe, cfg) -> DataFrame`.

- [ ] **Step 1: Write failing event deduplication test**

Feed auction context with accepted state true for 4 bars but `acceptance_event=True` only once. Assert exactly one `ACC_ABOVE_VAH` event is emitted.

- [ ] **Step 2: Write failing strong-absorption event test**

Assert possible absorption does not emit by default, strong absorption does.

- [ ] **Step 3: Write failing divergence event test**

Assert event timestamp is confirmation timestamp and pivot timestamp is preserved.

- [ ] **Step 4: Run failing tests**

```bash
pytest tests/test_events.py -v
```

- [ ] **Step 5: Implement event table**

Populate every context column listed in the spec and generate deterministic event IDs such as `BTCUSDT-15min-000001`.

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_events.py -v
```

- [ ] **Step 7: Commit**

```text
feat: emit deterministic research events
```

---

### Task 10: Outcome scoring, MFE/MAE, and validity labels

**Files:**
- Create: `backtest/outcomes.py`
- Create: `tests/test_outcomes.py`

**Interfaces:**
- Produces: `score_event_outcomes(events, parent_df, cfg) -> DataFrame`.

- [ ] **Step 1: Write failing forward-return test**

For bullish and bearish fixtures, assert directional return is positive when price moves in event direction at horizons 1, 3 and 5.

- [ ] **Step 2: Write failing MFE/MAE ordering test**

Fixture A reaches +0.5 ATR before -0.5 ATR → `VALID`.
Fixture B reaches -0.5 ATR first → `FAILED`.
Fixture C reaches neither in 5 bars → `NEUTRAL`.

- [ ] **Step 3: Run failing tests**

```bash
pytest tests/test_outcomes.py -v
```

- [ ] **Step 4: Implement outcome scorer**

Use event-bar ATR as normalization basis. Do not use any bar beyond configured evaluation horizon.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_outcomes.py -v
```

- [ ] **Step 6: Commit**

```text
feat: score event outcomes and excursions
```

---

### Task 11: Reports and end-to-end runner

**Files:**
- Create: `backtest/reporting.py`
- Create: `backtest/runner.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- Produces: `run_backtest(csv_path, symbol, cfg, output_dir) -> dict[str, Path]`.
- Produces: `events.csv` and `summary.csv`.

- [ ] **Step 1: Write failing integration fixture**

Create a temporary synthetic CSV with enough bars to produce at least one auction event and one absorption or divergence event. Assert runner creates both output files.

- [ ] **Step 2: Write failing summary aggregation assertions**

Assert summary contains grouping columns, sample count, valid/failed/neutral rates, average/median forward returns, average MFE ATR, average MAE ATR, and `LOW_SAMPLE` flag when count is below config minimum.

- [ ] **Step 3: Run failing integration test**

```bash
pytest tests/test_runner.py -v
```

- [ ] **Step 4: Implement runner pipeline**

Pipeline order:

```text
load 1m -> resample -> Delta -> volume/CVD -> profiles -> auction -> absorption -> divergence -> events -> outcomes -> reports
```

- [ ] **Step 5: Implement summary groups**

At minimum group by event type, event+pace, event+POC migration, event+value migration, event+CVD bias.

- [ ] **Step 6: Run integration test and full suite**

```bash
pytest -q
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```text
feat: add end to end event backtest runner
```

---

### Task 12: CLI and user documentation

**Files:**
- Create: `backtest/cli.py`
- Create: `docs/backtest.md`
- Modify: `README.md`
- Create: `tests/test_cli.py`

**Interfaces:**
- Produces: `python -m backtest.cli` command.

- [ ] **Step 1: Write failing CLI parser test**

Assert parser accepts:

```text
--csv
--symbol
--timeframe
--source-timezone
--session
--output-dir
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/test_cli.py -v
```

- [ ] **Step 3: Implement CLI**

Print loaded row count/date range, parent bar count, event counts, output paths, and warnings.

- [ ] **Step 4: Write docs**

Document expected CSV schema and example:

```bash
python -m backtest.cli \
  --csv data/BTCUSDT_1m.csv \
  --symbol BTCUSDT \
  --timeframe 15min \
  --source-timezone UTC \
  --session NewYork \
  --output-dir output/btc_15m
```

Explicitly state that Delta is an estimate reconstructed from 1-minute OHLCV.

- [ ] **Step 5: Run full suite**

```bash
pytest -q
```

- [ ] **Step 6: Commit**

```text
docs: add backtest cli and usage guide
```

---

### Task 13: RC9.1 Pine transition-marker bugfix

**Files:**
- Create: `tradingview/AuctionAI_OrderFlow_v1_RC9_1.pine`

**Interfaces:**
- Consumes: RC9 formulas unchanged.
- Produces: event booleans that transition once while HUD state persists.

- [ ] **Step 1: Define transition contract before edit**

Acceptance event condition:

```text
acceptedAboveEvent = acceptedAbove and not acceptedAbove[1]
acceptedBelowEvent = acceptedBelow and not acceptedBelow[1]
```

Rejection remains event-bar-only and is not latched.

- [ ] **Step 2: Copy RC9 into a new RC9.1 file**

Do not overwrite RC9.

- [ ] **Step 3: Replace marker predicates only**

Use transition booleans for Acceptance plotshapes while leaving `auctionState`, Delta, CVD, profile, migration and absorption formulas unchanged.

- [ ] **Step 4: Static review**

Confirm the RC9.1 diff is limited to title/version label and event-transition logic.

- [ ] **Step 5: User TradingView verification**

Ask user to compile RC9.1 and confirm:

- first Acceptance prints one marker
- following accepted bars print none
- after reset and new Acceptance, one fresh marker appears

Do not claim Pine compile success until user confirms TradingView compile/runtime.

- [ ] **Step 6: Commit**

```text
fix: emit rc9 acceptance markers on transitions
```

---

### Task 14: Final verification and research readiness check

**Files:**
- Review all backtest files and docs.

**Interfaces:**
- Produces: verified research baseline ready for real 1-minute data.

- [ ] **Step 1: Run full Python test suite**

```bash
pytest -q
```

Expected: all tests PASS, no warnings caused by project code.

- [ ] **Step 2: Run one synthetic CLI backtest**

```bash
python -m backtest.cli --csv tests/fixtures/sample_1m.csv --symbol TEST --timeframe 15min --source-timezone UTC --session NewYork --output-dir /tmp/auctionai-test
```

Expected: process exits successfully and creates `events.csv` and `summary.csv`.

- [ ] **Step 3: Inspect output columns**

Confirm event CSV includes all required context and outcome fields and summary includes grouping/statistics/LOW_SAMPLE.

- [ ] **Step 4: Check causality invariants**

Confirm no profile/reference calculation consumes rows with timestamps after the event timestamp and divergence fires only after pivot confirmation.

- [ ] **Step 5: Check documentation claim wording**

Confirm all docs say `estimated Universal Delta` and never call it true footprint/Bid-Ask Delta.

- [ ] **Step 6: Record verification evidence**

Report exact commands and test outputs before claiming the Python harness is complete. Pine RC9.1 remains separately dependent on the user's TradingView compile verification.

- [ ] **Step 7: Commit any final verification/docs corrections**

```text
chore: finalize backtest research baseline
```
