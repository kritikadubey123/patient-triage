"""Triage endpoints: submit vitals -> get a prioritised result, and read the queue."""
import logging
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import MLPrediction, TriageRecord
from schemas import TriageCreate, TriageResponse

logger = logging.getLogger("triage")

router = APIRouter(prefix="/api", tags=["triage"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_model_bundle(request: Request) -> dict:
    """Return the model artifact that main.py loaded at startup."""
    bundle = getattr(request.app.state, "model_bundle", None)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Run train.py and restart the server.",
        )
    return bundle


ModelBundle = Annotated[dict, Depends(get_model_bundle)]


def run_inference(bundle: dict, data: TriageCreate) -> tuple[str, float]:
    """Synchronous, CPU-bound prediction. Returns (priority label, confidence)."""
    # Build the input in the exact feature order saved by train.py, as a DataFrame
    # so column names match what the pipeline was fitted on.
    row = {name: getattr(data, name) for name in bundle["features"]}
    frame = pd.DataFrame([row], columns=bundle["features"])

    probabilities = bundle["pipeline"].predict_proba(frame)[0]
    best = int(probabilities.argmax())
    return bundle["labels"][best], round(float(probabilities[best]), 4)


@router.post("/triage", response_model=TriageResponse, status_code=status.HTTP_201_CREATED)
async def create_triage(payload: TriageCreate, db: DbSession, bundle: ModelBundle):
    # 1. Inference first: if the model fails, nothing has been written to the DB.
    #    predict_proba is blocking CPU work, so run it in a worker thread instead
    #    of freezing the event loop for every other request.
    try:
        priority, confidence = await run_in_threadpool(run_inference, bundle, payload)
    except Exception:
        logger.exception("Model inference failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compute a triage priority.",
        )

    # 2. Save the record and its prediction in ONE transaction (all or nothing).
    record = TriageRecord(**payload.model_dump())
    record.prediction = MLPrediction(predicted_priority=priority, confidence_score=confidence)

    try:
        db.add(record)  # the prediction is saved too, via the relationship cascade
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database write failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the triage record.",
        )

    return record


@router.get("/queue", response_model=list[TriageResponse])
async def get_queue(
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
):
    """Prioritised queue: Critical first, then Urgent, then Standard.
    Within the same priority, whoever has waited longest comes first."""
    priority_rank = case(
        (MLPrediction.predicted_priority == "Critical", 0),
        (MLPrediction.predicted_priority == "Urgent", 1),
        else_=2,
    )

    stmt = (
        select(TriageRecord)
        .join(MLPrediction)
        # selectinload fetches predictions with one extra query. Async SQLAlchemy
        # forbids lazy loading, so relationships must be loaded explicitly.
        .options(selectinload(TriageRecord.prediction))
        .order_by(priority_rank, TriageRecord.created_at.asc())
        .limit(limit)
    )

    try:
        result = await db.execute(stmt)
    except SQLAlchemyError:
        logger.exception("Database read failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load the queue.",
        )

    return result.scalars().all()