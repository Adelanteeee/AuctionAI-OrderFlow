# AuctionAI Order Flow

Standalone TradingView Pine Script v6 order-flow evidence toolkit.

## v1 features

- Delta and Delta %
- CVD with Continuous / Daily / Session reset
- Relative Volume
- Effort vs Result
- Multi-factor Absorption
- Price/Delta divergence
- Price/CVD divergence
- Priority-based candle coloring
- Daily or Session Volume Profile
- POC / VAH / VAL
- Optional full profile histogram
- Diagnostics table and Data Window outputs

## Editions

### Universal
`tradingview/AuctionAI_OrderFlow_v1.pine`

Uses `request.security_lower_tf()` and classifies lower-timeframe volume by intrabar candle direction. This is **directional-volume estimation**, not true Bid/Ask aggressor Delta.

### Footprint (Premium/Ultimate)
`tradingview/AuctionAI_OrderFlow_v1_Footprint.pine`

Uses TradingView `request.footprint()` for the bar's footprint buy volume, sell volume, and Delta. TradingView restricts footprint requests to Premium/Ultimate plans.

## Recommended starting settings

- 5m chart -> 1m lower timeframe
- Volume average: 20
- High volume: 1.5x average
- Strong Delta: 20%
- Pivot strength: 3 / 3
- Profile rows: 24
- Value Area: 70%

## Philosophy

AuctionAI Order Flow v1 provides **evidence, not entry/exit signals**. Candle states describe pressure, participation, absorption, divergence, and effort/result relationships.

## Public-code note

The implementation is original. A user-supplied LuxAlgo Volume Delta script was used only as a conceptual reference for lower-timeframe directional-volume estimation; its source code is not copied into this repository.