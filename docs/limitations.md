# Limitations

- Universal Delta is a lower-timeframe directional-volume estimate, not true Bid/Ask aggressor Delta.
- TradingView footprint requests require Premium or Ultimate. The Footprint edition will not be usable on lower-tier plans.
- Forex and many CFD feeds can expose tick volume rather than centralized traded volume.
- Confirmed-pivot divergences are intentionally delayed by `pivotRight` bars to avoid using unconfirmed pivots.
- Session presets use the symbol exchange timezone through Pine's `time()` session behavior.
- Volume Profile assigns each bar's full volume to its HLC3 price row. It is intentionally lightweight and may differ from TradingView's native profile, which can use lower-timeframe distribution internally.
- Historical intrabar coverage depends on TradingView data availability and the chosen lower timeframe.
- No trade signal, order execution, or profitability claim is produced by v1.