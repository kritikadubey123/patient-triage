"""Pydantic schemas: request validation + response shapes."""
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from models import Priority

# Keep these in sync with BOUNDS in train.py: the API should never feed the
# model values outside the range it was trained on.
VITAL_LIMITS = {
    "age": (0, 110, "years"),
    "heart_rate": (30, 220, "bpm"),
    "systolic_bp": (50, 260, "mmHg"),
    "temperature": (32.0, 43.0, "°C"),
}


class TriageCreate(BaseModel):
    """Incoming patient vitals."""

    model_config = ConfigDict(str_strip_whitespace=True)

    patient_name: str = Field(min_length=1, max_length=100)
    age: int
    heart_rate: int
    systolic_bp: int
    temperature: float

    @field_validator("patient_name")
    @classmethod
    def name_must_contain_a_letter(cls, v: str) -> str:
        if not any(ch.isalpha() for ch in v):
            raise ValueError("patient_name must contain at least one letter")
        return v

    @field_validator("age", "heart_rate", "systolic_bp", "temperature")
    @classmethod
    def vital_must_be_realistic(cls, v: float, info: ValidationInfo) -> float:
        # One validator, four fields. info.field_name tells us which one is being
        # checked. NaN/inf fail automatically because comparisons with them are False.
        low, high, unit = VITAL_LIMITS[info.field_name]
        if not (low <= v <= high):
            raise ValueError(f"{info.field_name} must be between {low} and {high} {unit}")
        return v


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_priority: Priority
    confidence_score: float


class TriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # allows building from ORM objects

    id: int
    patient_name: str
    age: int
    heart_rate: int
    systolic_bp: int
    temperature: float
    created_at: datetime
    prediction: PredictionOut

    @field_validator("created_at")
    @classmethod
    def assume_utc(cls, v: datetime) -> datetime:
        # SQLite drops timezone info. We always store UTC, so re-attach it;
        # the JSON then ends in +00:00 and the browser converts to local time.
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v