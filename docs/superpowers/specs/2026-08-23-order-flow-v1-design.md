# AuctionAI Order Flow v1 — Design Specification

Date: 2026-08-23
Status: Proposed for user review
Target: TradingView Pine Script v6
Repository: AuctionAI-OrderFlow (public, standalone)

## 1. Scope

AuctionAI Order Flow v1 is a standalone TradingView indicator focused only on order-flow evidence and volume-profile context. It must not depend on or modify the existing AuctionAI repository or v5.0 codebase.

Included in v1:
- Delta
- CVD
- Volume
- Absorption
- Effort vs Result
- Price/Delta divergence
- Price/CVD divergence
- Conditional candle coloring
- Selectable Daily / Session Volume Profile
- POC / VAH / VAL
- Optional full profile histogram

Explicitly excluded from v1:
- AuctionAI v5.0 lifecycle logic
- Acceptance/retest/outcome-memory logic
- Trade entry/exit signals
- Automated strategy execution
- ML/self-learning components
- Manual arbitrary-anchor FRVP

## 2. Design Principles

1. Evidence, not signal generation. The indicator describes order-flow conditions; it does not produce buy/sell commands.
2. Hybrid data acquisition. Prefer TradingView footprint data when available; fall back to lower-timeframe intrabar estimation when footprint is unavailable.
3. Source transparency. The active Delta source must be visible to the user so estimated intrabar Delta is never presented as true Bid/Ask Delta.
4. Independent engines. Delta, CVD, Volume, Absorption, Effort/Result, Divergence and Profile calculations must be logically separated.
5. Public-repository hygiene. Do not copy third-party licensed source code. The supplied LuxAlgo script is a behavioral reference only; implementation must be original.
6. Configurable visuals. Users can keep the chart minimal or enable detailed panels/profile plots from Settings.

## 3. Data Architecture

### 3.1 Hybrid Delta Engine

Mode: Auto / Footprint / Intrabar

Auto behavior:
1. Use TradingView footprint-derived buy/sell volume when supported by the account/runtime.
2. Otherwise use lower-timeframe intrabar estimation.
3. Expose active source as `Footprint` or `Intrabar Estimate`.

Canonical engine output:
- buyVolume
- sellVolume
- neutralVolume (when applicable)
- totalClassifiedVolume
- delta
- deltaPercent
- sourceQuality/sourceLabel

### 3.2 Intrabar Fallback

Use `request.security_lower_tf()` with an automatically selected or user-selected lower timeframe.

Base classification:
- lower-TF candle close > open -> buy volume
- lower-TF candle close < open -> sell volume
- lower-TF candle close == open -> neutral volume

Delta:
`buyVolume - sellVolume`

Delta percent:
`delta / parentBarVolume` when parentBarVolume > 0.

The fallback is an estimate of directional volume, not exchange Bid/Ask aggression.

### 3.3 CVD Engine

CVD is derived only from the canonical Delta output so downstream logic is data-source agnostic.

Outputs:
- raw cumulative delta
- session-reset CVD option
- daily-reset CVD option
- continuous CVD option
- CVD slope/bias
- optional smoothed CVD

Default v1: continuous CVD, with reset mode selectable in Settings.

## 4. Volume Engine

Inputs:
- current volume
- moving average volume baseline
- configurable lookback

Derived values:
- relativeVolume = volume / averageVolume
- Normal
- High
- Extreme

Thresholds are configurable with sensible defaults.

Volume source limitations must remain visible for symbols where TradingView exposes tick volume instead of centralized traded volume.

## 5. Effort vs Result Engine

Effort = relative volume.

Result uses normalized price displacement and candle efficiency, using ATR and/or bar range so comparisons remain meaningful across instruments.

Core states:
- High Effort / High Result
- High Effort / Low Result
- Low Effort / High Result
- Low Effort / Low Result

`High Effort / Low Result` is evidence of potential absorption or opposing liquidity but is not sufficient on its own to label absorption.

## 6. Absorption Engine

Absorption must require confluence, not simply high volume plus a small body.

Potential bullish/selling-absorption evidence:
- meaningful sell-side Delta pressure
- high relative volume / effort
- limited downside result
- favorable close location and/or lower wick response

Potential bearish/buying-absorption evidence:
- meaningful buy-side Delta pressure
- high relative volume / effort
- limited upside result
- unfavorable close location and/or upper wick response

Outputs:
- No Absorption
- Possible Selling Absorption
- Strong Selling Absorption
- Possible Buying Absorption
- Strong Buying Absorption

Terminology refers to which aggressive side is being absorbed.

## 7. Divergence Engine

Two families:

### Price vs Delta
- Bullish: price makes a lower low while Delta fails to make a corresponding lower low / improves.
- Bearish: price makes a higher high while Delta fails to make a corresponding higher high / weakens.

### Price vs CVD
- Bullish: price lower low with CVD higher low / non-confirmation.
- Bearish: price higher high with CVD lower high / non-confirmation.

Detection should use confirmed pivots and configurable pivot strength to limit noisy one-bar comparisons and reduce repaint-like behavior.

## 8. Candle State and Coloring

Candle colors must express evidence states, not trade signals.

Priority order prevents conflicting colors:
1. Strong Absorption
2. Strong Divergence
3. Strong directional Delta + Volume confirmation
4. High Effort / Low Result
5. Normal candle color

Settings:
- Enable/disable candle coloring
- Enable/disable each evidence category
- User-selectable colors
- Optional markers/labels separate from bar color

Initial named states:
- Strong Buying
- Strong Selling
- Buying Absorbed
- Selling Absorbed
- Bullish Divergence
- Bearish Divergence
- High Effort / Low Result
- Neutral

## 9. Volume Profile Engine

Profile mode in Settings:
- Off
- Daily
- Session

Session choices:
- Asia
- London
- New York
- Custom

Display mode:
- Levels Only
- Full Profile

Levels:
- POC
- VAH
- VAL

Full Profile:
- price-row volume histogram
- configurable row count
- configurable value-area percentage, default 70%
- optional developing POC

The Profile Engine is isolated from the Delta Engine so future Delta-by-price profiles or fixed-range profiles can be added without rewriting the order-flow core.

## 10. Display Architecture

Main-chart overlays:
- conditional candle colors
- absorption/divergence markers
- volume profile histogram when enabled
- POC/VAH/VAL

Order-flow panel option:
- Delta histogram
- CVD line
- Volume / Relative Volume

Because Pine has practical display constraints, v1 should prioritize a single script that can expose panel series through plots/data-window while keeping profile/candle evidence on the chart. If TradingView limitations prevent a clean combined overlay + separate pane experience in one script, split into two coordinated scripts in the same repository:
1. `AuctionAI_OrderFlow_v1_Overlay.pine`
2. `AuctionAI_OrderFlow_v1_Panel.pine`

Both scripts must share equivalent settings and calculation rules.

## 11. Settings Groups

- Data Source
- Delta
- CVD
- Volume
- Effort vs Result
- Absorption
- Divergence
- Candle Coloring
- Volume Profile
- Sessions
- Display
- Diagnostics

Diagnostics should optionally show:
- active Delta source
- selected lower timeframe
- intrabar count
- volume-data availability
- current profile mode/session

## 12. Error and Degradation Handling

- No lower-TF data: return neutral/NA evidence rather than fabricate Delta.
- Footprint unavailable: Auto mode falls back to intrabar estimation.
- Insufficient pivot history: divergence remains inactive.
- No volume: volume-derived states disabled for the bar.
- Invalid/custom session boundaries: profile does not calculate until a valid session exists.
- Profile resource pressure: cap row count and drawing objects to Pine limits.

## 13. Validation Strategy

Manual validation on multiple symbols and market types:
- XAUUSD / CFD or spot feed
- major FX pair
- index CFD / futures-compatible symbol if available
- crypto pair

Validation cases:
- Delta sign and magnitude sanity checks
- CVD continuity/reset behavior
- intrabar fallback against reference Volume Delta behavior
- absorption examples with high effort / low result
- divergence pivot confirmation
- daily profile reset
- Asia/London/New York/custom session reset
- POC/VAH/VAL consistency
- settings toggles do not affect hidden calculations unexpectedly

## 14. Repository Layout

```text
AuctionAI-OrderFlow/
  README.md
  LICENSE
  tradingview/
    AuctionAI_OrderFlow_v1.pine
  docs/
    methodology.md
    limitations.md
    superpowers/specs/
      2026-08-23-order-flow-v1-design.md
```

If overlay/panel separation becomes necessary:

```text
tradingview/
  AuctionAI_OrderFlow_v1_Overlay.pine
  AuctionAI_OrderFlow_v1_Panel.pine
```

## 15. Licensing

The new repository will be public. Do not include copied LuxAlgo implementation code. The supplied LuxAlgo script is licensed CC BY-NC-SA 4.0 and is used only as a conceptual/reference implementation for lower-timeframe directional-volume estimation.

A repository license for our original code will be chosen separately before public release if needed; until explicitly selected, do not claim permissive reuse rights beyond GitHub's normal viewing/forking behavior.

## 16. Success Criteria for v1

v1 is successful when:
- Hybrid Delta operates with transparent source labeling.
- CVD derives consistently from the selected Delta source.
- Volume and Effort/Result states are stable and configurable.
- Absorption requires multi-factor evidence.
- Price/Delta and Price/CVD divergences use confirmed pivots.
- Candle coloring is deterministic and conflict-prioritized.
- Daily and session profiles can be selected from Settings.
- POC/VAH/VAL and optional full profile render correctly.
- No AuctionAI v5.0 code or repository is modified.
