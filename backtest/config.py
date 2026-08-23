from dataclasses import dataclass

@dataclass(slots=True)
class BacktestConfig:
    parent_timeframe: str = '15min'
    body_weight: float = 0.65
    close_weight: float = 0.35
    pressure_cap: float = 0.90
    min_tick: float = 0.01
    cvd_smoothing: int = 5
    volume_sma: int = 20
    high_volume_mult: float = 1.5
    extreme_volume_mult: float = 2.5
    pace_expand: float = 115.0
    pace_contract: float = 85.0
    atr_length: int = 14
    result_threshold_atr: float = 0.5
    absorption_min_delta_pct: float = 20.0
    profile_rows: int = 28
    value_area_pct: float = 70.0
    acceptance_closes: int = 2
    poc_tolerance_atr: float = 0.05
    rejection_penetration_atr: float = 0.03
    value_shift_threshold: float = 0.15
    outcome_threshold_atr: float = 0.5
    outcome_horizon: int = 5
    session_name: str = 'NewYork'
