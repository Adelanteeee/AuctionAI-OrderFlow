# Methodology

## Delta — Universal edition

The Universal edition requests lower-timeframe OHLCV arrays with `request.security_lower_tf()`. Each intrabar is classified as buy volume when `close > open`, sell volume when `close < open`, and neutral when `close == open`. Bar Delta is buy volume minus sell volume. Delta % is Delta divided by the parent bar's volume.

This is an estimate of directional volume, not direct Bid/Ask aggressor data.

## Delta — Footprint edition

The Footprint edition uses TradingView's `request.footprint()` and reads the footprint object's total buy volume, sell volume, total volume and Delta.

## CVD

CVD accumulates the canonical Delta stream. Reset modes are Continuous, Daily and selected Session.

## Relative Volume

Relative Volume = current volume / SMA(volume, length). The default High threshold is 1.5x and Extreme threshold is 2.5x.

## Effort vs Result

Effort is relative volume. Result is absolute close-to-close displacement relative to ATR. High effort with low result is treated as potential opposing liquidity, not absorption by itself.

## Absorption

Absorption requires one-sided Delta pressure, high effort, limited result, and a rejection/close-location condition. The labels describe the aggressive side being absorbed: Selling Absorption means aggressive selling appears absorbed; Buying Absorption means aggressive buying appears absorbed.

## Divergence

Divergence uses confirmed price pivots only. Price lower-low with improving Delta/CVD is bullish non-confirmation. Price higher-high with weakening Delta/CVD is bearish non-confirmation. Markers are plotted back on the pivot bar after confirmation.

## Candle coloring priority

1. Strong Absorption
2. Strong Delta + CVD divergence
3. Strong directional Delta with high volume
4. High Effort / Low Result
5. Neutral / native candle color

## Volume Profile

The current Daily or selected Session profile stores each participating bar's HLC3 and volume. Stored prices are bucketed into configurable rows between the profile low and high. POC is the highest-volume row. Value Area expands from POC toward the larger adjacent row until the configured percentage of profile volume is included.