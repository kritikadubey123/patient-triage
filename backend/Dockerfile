FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite+aiosqlite:////data/triage.db

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the model INSIDE the image build. This guarantees triage_model.pkl was
# created by the exact scikit-learn version installed above (a .pkl copied from
# another machine can fail to load if the versions differ). It is still the same
# offline script; the API only ever loads the finished file at startup.
RUN python train.py

# Run as a non-root user. /data holds the SQLite file and is mounted as a volume.
RUN useradd --create-home app && mkdir /data && chown app /data
USER app

EXPOSE 8000

# python:slim has no curl, so use Python itself for the health probe.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]