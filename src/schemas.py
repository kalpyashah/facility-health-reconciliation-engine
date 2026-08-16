from datetime import datetime
from enum import Enum
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator


class EventSource(str, Enum):
    CONTRACTOR = "Contractor"
    MANUAL = "Manual"
    IOT = "IoT"


class Subsystem(str, Enum):
    HVAC = "HVAC"
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


SOURCE_PRIORITY = {
    EventSource.CONTRACTOR: 1,  # Highest priority
    EventSource.MANUAL: 2,
    EventSource.IOT: 3,         # Lowest priority
}


SEVERITY_WEIGHT = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class RawEvent(BaseModel):
    event_id: str
    event_type: str
    source: str
    timestamp: datetime
    subsystem: str
    status: str
    severity: Optional[str] = "Low"
    user_id: Optional[str] = None
    work_order_id: Optional[str] = None
    device_id: Optional[str] = None
    value: Optional[Union[float, int]] = None

    @field_validator("source", mode="before")
    def normalize_source(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Source must be a non-empty string")
        val = v.strip().capitalize()
        if val in ["Iot", "I-o-t", "Iotelem"]:
            return EventSource.IOT.value
        if val in ["Contractor", "Vendor"]:
            return EventSource.CONTRACTOR.value
        if val in ["Manual", "Inspection"]:
            return EventSource.MANUAL.value
        return val

    @field_validator("subsystem", mode="before")
    def normalize_subsystem(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Subsystem must be a non-empty string")
        val = v.strip().upper()
        if val not in [s.value for s in Subsystem]:
            raise ValueError(f"Unknown subsystem: {val}")
        return val


class NormalizedEvent(BaseModel):
    event_id: str
    source: EventSource
    timestamp: datetime
    subsystem: Subsystem
    status: str
    severity: Severity
    user_id: Optional[str] = None
    work_order_id: Optional[str] = None
    device_id: Optional[str] = None
    value: Optional[float] = None

    @property
    def priority(self) -> int:
        return SOURCE_PRIORITY[self.source]


class AuditDecision(BaseModel):
    subsystem: str
    window_start: datetime
    window_end: datetime
    reconciled_state: str
    winning_event_id: str
    winning_source: str
    rule_applied: str
    reasoning: str
    competing_events: list[str]