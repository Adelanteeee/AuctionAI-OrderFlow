from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class ProfileLevels:
    poc: float
    vah: float
    val: float

@dataclass(frozen=True, slots=True)
class EventRecord:
    event_id: str
    timestamp: datetime
    event_type: str
    direction: str

@dataclass(frozen=True, slots=True)
class OutcomeResult:
    label: str
    mfe_atr: float
    mae_atr: float
