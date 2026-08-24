def absorption_score(*, delta_pct, relative_volume, high_result, lower_wick_ratio, upper_wick_ratio,
                     close_location, min_delta_pct=20.0, high_vol_mult=1.5):
    sell_pressure = delta_pct is not None and delta_pct <= -min_delta_pct
    buy_pressure = delta_pct is not None and delta_pct >= min_delta_pct
    delta_strength = min(1.0, abs(delta_pct)/max(min_delta_pct,1.0)) if delta_pct is not None else 0.0
    effort_strength = min(1.0, relative_volume/max(high_vol_mult,.01)) if relative_volume is not None else 0.0
    low_result_strength = 0.0 if high_result else 1.0
    sell_reject = min(1.0, (lower_wick_ratio+close_location)/1.2)
    buy_reject = min(1.0, (upper_wick_ratio+(1.0-close_location))/1.2)
    sell = delta_strength*30+effort_strength*25+low_result_strength*20+sell_reject*25 if sell_pressure else 0.0
    buy = delta_strength*30+effort_strength*25+low_result_strength*20+buy_reject*25 if buy_pressure else 0.0
    score = max(sell,buy)
    side = 'SELLING ABSORBED' if sell>buy else 'BUYING ABSORBED' if buy>sell else 'NONE'
    state = ('STRONG SELLING ABSORPTION' if sell>=75 else 'STRONG BUYING ABSORPTION' if buy>=75 else
             'POSSIBLE SELLING ABSORPTION' if sell>=55 else 'POSSIBLE BUYING ABSORPTION' if buy>=55 else 'NO ABSORPTION')
    return score, side, state
