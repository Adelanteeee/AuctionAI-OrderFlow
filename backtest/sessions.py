from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SessionSpec:
    name: str
    timezone: str
    start_minute: int
    end_minute: int

SESSION_PRESETS = {
    'Asia': SessionSpec('Asia','Asia/Tokyo',9*60,18*60),
    'London': SessionSpec('London','Europe/London',8*60,17*60),
    'NewYork': SessionSpec('NewYork','America/New_York',9*60+30,16*60),
}

def get_session_spec(name: str) -> SessionSpec:
    try:
        return SESSION_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f'unsupported session: {name}') from exc

def session_membership(ts, spec: SessionSpec):
    local = ts.tz_convert(spec.timezone)
    minute = local.hour*60+local.minute
    in_session = spec.start_minute <= minute < spec.end_minute
    elapsed = minute-spec.start_minute if in_session else None
    return in_session, local.date(), elapsed
