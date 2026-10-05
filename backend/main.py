"""FastAPI app entry point. Run with:  uvicorn main:app --reload"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import triage

logger = logging.getLogger("triage")
logging.basicConfig(level=logging.INFO)

# triage_model.pkl sits next to this file (backend/ root). Anchoring on __file__
# means it works no matter which directory you launch uvicorn from.
MODEL_PATH = Path(__file__).parent / "triage_model.pkl"

# Which browser origins may call the API. Comma-separated, overridable via env var.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    # Create tables if they don't exist yet. (Fine for a project this size;
    # a larger team would use Alembic migrations instead.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load the model ONCE and keep it in memory for every request.
    if MODEL_PATH.exists():
        app.state.model_bundle = joblib.load(MODEL_PATH)
        logger.info("Loaded model from %s", MODEL_PATH)
    else:
        app.state.model_bundle = None
        logger.error("Model file not found at %s - run train.py first", MODEL_PATH)

    yield

    # ---- shutdown ----
    await engine.dispose()


app = FastAPI(title="Intelligent Patient Triage API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(triage.router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "model_loaded": app.state.model_bundle is not None}
