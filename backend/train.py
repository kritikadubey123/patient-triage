"""
Offline training script for the Intelligent Patient Triage System.

Run once (or whenever you want to retrain):
    cd backend
    python -m ml.train

Output: backend/ml/triage_model.pkl
The FastAPI app loads this file at startup (lifespan) and never trains in-process.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SEED = 42
N_SAMPLES = 6000
MODEL_PATH = Path(__file__).parent / "triage_model.pkl"

# Feature ORDER matters at inference time. We save it next to the model so the
# API builds its input in exactly the same order.
FEATURES = ["age", "heart_rate", "systolic_bp", "temperature"]
LABELS = ["Standard", "Urgent", "Critical"]  # increasing severity

# Realistic bounds. Reuse the same ranges in the Pydantic validators (Phase 2)
# so the API never sends the model values it has never seen.
BOUNDS = {
    "age": (0, 110),
    "heart_rate": (30, 220),      # beats per minute
    "systolic_bp": (50, 260),     # mmHg
    "temperature": (32.0, 43.0),  # degrees Celsius
}


# ---------------------------------------------------------------------------
# 1. Synthetic data
# ---------------------------------------------------------------------------
def severity_score(row: pd.Series) -> int:
    """Rule-based 'ground truth', loosely inspired by early-warning scores.
    Each abnormal vital adds points; more extreme values add more."""
    score = 0

    hr = row["heart_rate"]
    if hr > 130 or hr < 45:
        score += 3
    elif hr > 110 or hr < 55:
        score += 2
    elif hr > 100 or hr < 60:
        score += 1

    bp = row["systolic_bp"]
    if bp < 80 or bp > 200:
        score += 3
    elif bp < 90 or bp > 180:
        score += 2
    elif bp < 100 or bp > 140:
        score += 1

    temp = row["temperature"]
    if temp > 40 or temp < 35:
        score += 3
    elif temp > 39:
        score += 2
    elif temp > 38:
        score += 1

    # Very young and elderly patients deteriorate faster
    if row["age"] < 5 or row["age"] > 75:
        score += 1

    return score


def score_to_label(score: int) -> int:
    if score >= 5:
        return 2  # Critical
    if score >= 2:
        return 1  # Urgent
    return 0      # Standard


def generate_dataset(n: int = N_SAMPLES, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Mixture: ~55% healthy-looking, ~45% abnormal, so all classes are represented.
    is_abnormal = rng.random(n) < 0.45

    heart_rate = np.where(is_abnormal, rng.normal(100, 32, n), rng.normal(78, 10, n))
    systolic_bp = np.where(is_abnormal, rng.normal(120, 38, n), rng.normal(120, 12, n))
    temperature = np.where(is_abnormal, rng.normal(37.9, 1.4, n), rng.normal(36.8, 0.4, n))
    age = rng.integers(*BOUNDS["age"], size=n)

    df = pd.DataFrame(
        {
            "age": age,
            "heart_rate": heart_rate,
            "systolic_bp": systolic_bp,
            "temperature": temperature,
        }
    )

    # Clip to the physiological bounds the API will also enforce
    for col, (lo, hi) in BOUNDS.items():
        df[col] = df[col].clip(lo, hi)

    df["heart_rate"] = df["heart_rate"].round().astype(int)
    df["systolic_bp"] = df["systolic_bp"].round().astype(int)
    df["temperature"] = df["temperature"].round(1)

    df["label"] = df.apply(severity_score, axis=1).map(score_to_label)

    # ~3% label noise (a clinician's judgement isn't a perfect formula).
    # This keeps the model from simply memorising our rules and makes
    # predict_proba confidences more realistic than a constant 1.0.
    noisy = rng.random(n) < 0.03
    shift = rng.choice([-1, 1], size=n)
    df.loc[noisy, "label"] = np.clip(df.loc[noisy, "label"] + shift[noisy], 0, 2)

    return df


# ---------------------------------------------------------------------------
# 2. Train + evaluate
# ---------------------------------------------------------------------------
def build_pipeline() -> Pipeline:
    # Random Forest doesn't strictly need scaling, but a scaler inside the
    # Pipeline means the exact same preprocessing is applied at inference,
    # and it lets you swap in a scale-sensitive model later (e.g. logistic reg).
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def main() -> None:
    df = generate_dataset()
    print("Class distribution:")
    print(df["label"].map(dict(enumerate(LABELS))).value_counts(normalize=True).round(3))

    X = df[FEATURES]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    pipeline = build_pipeline()

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1_macro")
    print(f"\n5-fold CV macro-F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    print("\nHold-out test report:")
    print(classification_report(y_test, y_pred, target_names=LABELS, digits=3))
    print("Confusion matrix (rows = true, cols = predicted):")
    print(pd.DataFrame(confusion_matrix(y_test, y_pred), index=LABELS, columns=LABELS))

    importances = pipeline.named_steps["clf"].feature_importances_
    print("\nFeature importances:")
    for name, imp in sorted(zip(FEATURES, importances), key=lambda t: -t[1]):
        print(f"  {name:<12} {imp:.3f}")

    # Save the pipeline together with metadata the API needs.
    artifact = {
        "pipeline": pipeline,
        "features": FEATURES,
        "labels": LABELS,  # index i == class i from the model
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"\nSaved model artifact to {MODEL_PATH}")

    # Sanity check: reload and predict one obviously critical patient
    loaded = joblib.load(MODEL_PATH)
    sample = pd.DataFrame([[82, 145, 70, 40.5]], columns=loaded["features"])
    proba = loaded["pipeline"].predict_proba(sample)[0]
    best = int(np.argmax(proba))
    print(f"Sanity check -> {loaded['labels'][best]} (confidence {proba[best]:.2f})")


if __name__ == "__main__":
    main()