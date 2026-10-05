"""SQLAlchemy ORM models (2.0 typed style)."""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Priority(str, enum.Enum):
    CRITICAL = "Critical"
    URGENT = "Urgent"
    STANDARD = "Standard"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TriageRecord(Base):
    __tablename__ = "triage_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int]
    heart_rate: Mapped[int]
    systolic_bp: Mapped[int]
    temperature: Mapped[float] = mapped_column(Float)
    # Set in Python (not server_default) so the value exists on the object right
    # after flush, with no extra async round-trip to read it back.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    # One record -> one prediction. Deleting a record deletes its prediction.
    prediction: Mapped[Optional["MLPrediction"]] = relationship(
        back_populates="record", uselist=False, cascade="all, delete-orphan"
    )


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("triage_records.id", ondelete="CASCADE"), unique=True, index=True
    )
    predicted_priority: Mapped[str] = mapped_column(String(16), index=True)
    confidence_score: Mapped[float] = mapped_column(Float)

    record: Mapped["TriageRecord"] = relationship(back_populates="prediction")