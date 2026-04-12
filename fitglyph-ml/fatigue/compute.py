"""
ACWR + Fatigue Engine.

Computes Acute:Chronic Workload Ratio, training monotony, and strain
from the user's workout log in the Flask app's SQLite database.

Math (from ML_FEATURES.md):
  Volume Load per session : VL = Σ(sets × reps × weight) — bodyweight excluded
  Acute Load              : EWMA(VL, span=7,  adjust=False)  — ~7-day decay
  Chronic Load            : EWMA(VL, span=28, adjust=False)  — ~28-day decay
  ACWR                    : acute / chronic  (0 if chronic is 0)
  Monotony                : mean(VL_7d) / std(VL_7d, ddof=1)  (0 if std is 0)
  Strain                  : sum(VL_7d) × monotony

adjust=False uses the recursive EWMA formula (λ = 1 − 2/(span+1)), which
matches the sports science definition in the spec. pandas defaults to
adjust=True, which gives different results on short series.

ACWR zones:
  < 0.8          → "undertrained"
  0.8 – 1.3      → "optimal"
  1.3 – 1.5      → "caution"
  > 1.5          → "high_risk"

Cold start:
  days_of_data < 7  → HTTP 422  (hard error, cannot compute)
  days_of_data < 28 → HTTP 200 with "warning" field (EWMA less reliable)
"""

import json
import os
from collections import defaultdict
from datetime import date, datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from fatigue.history import format_history_payload

load_dotenv()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///c:/Users/ramse/gymlog/instance/gymlog.db",
)
# check_same_thread=False required for SQLite under FastAPI's thread-pool executor
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

# { user_id: {"data": <status payload dict>, "computed_at": datetime (UTC)} }
_cache: dict[int, dict] = {}
_CACHE_TTL_HOURS = 24

_MIN_DAYS_HARD = 7    # below this: refuse to compute
_MIN_DAYS_WARN = 28   # below this: compute but warn

router = APIRouter()

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_get(user_id: int) -> dict | None:
    entry = _cache.get(user_id)
    if entry is None:
        return None
    age = datetime.now(timezone.utc) - entry["computed_at"]
    if age.total_seconds() > _CACHE_TTL_HOURS * 3600:
        del _cache[user_id]
        return None
    return entry["data"]


def _cache_set(user_id: int, data: dict) -> None:
    _cache[user_id] = {"data": data, "computed_at": datetime.now(timezone.utc)}


def _cache_invalidate(user_id: int) -> None:
    _cache.pop(user_id, None)


# ---------------------------------------------------------------------------
# Database fetch
# ---------------------------------------------------------------------------


def _fetch_raw_rows(user_id: int) -> list[dict]:
    """
    Fetch all completed (non-draft) workouts and their exercises for a user.

    Uses LEFT JOIN so rest-day workouts (no exercise rows) still appear,
    contributing a 0-VL day to the EWMA series.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    w.id          AS workout_id,
                    w.date        AS workout_date,
                    w.is_rest_day,
                    e.id          AS exercise_id,
                    e.sets,
                    e.reps,
                    e.weight,
                    e.set_data
                FROM workout w
                LEFT JOIN exercise e ON e.workout_id = w.id
                WHERE w.user_id = :user_id
                  AND w.is_draft = 0
                ORDER BY w.date ASC
            """),
            {"user_id": user_id},
        )
        return [dict(row._mapping) for row in result]


# ---------------------------------------------------------------------------
# Volume Load computation
# ---------------------------------------------------------------------------


def _vl_from_set_data(set_data_raw: str) -> float | None:
    """
    Parse set_data JSON and sum reps × weight across all sets.
    Returns None if set_data is absent, empty, or unparseable.
    """
    if not set_data_raw:
        return None
    try:
        sets = json.loads(set_data_raw)
        if not sets:
            return None
        total = 0.0
        for s in sets:
            w = s.get("weight")
            r = s.get("reps", 0) or 0
            if w and w > 0:
                total += r * w
        return total
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def _compute_workout_vl(exercise_rows: list[dict]) -> float:
    """
    Compute Volume Load for a single workout from its exercise rows.

    Preference order:
      1. set_data JSON (per-set reps × weight)
      2. Top-level sets × reps × weight

    Bodyweight exercises (weight is None or 0) are excluded from VL.
    Rest-day rows contain NULL exercise columns and contribute 0.
    """
    total = 0.0
    for row in exercise_rows:
        # Rest day: exercise columns are NULL from LEFT JOIN
        if row.get("exercise_id") is None:
            continue

        # Try set_data first
        vl = _vl_from_set_data(row.get("set_data"))
        if vl is not None:
            total += vl
            continue

        # Fallback: top-level fields
        w = row.get("weight")
        s = row.get("sets") or 0
        r = row.get("reps") or 0
        if w and w > 0:
            total += s * r * w

    return total


# ---------------------------------------------------------------------------
# Daily VL series construction
# ---------------------------------------------------------------------------


def _parse_workout_date(raw) -> date:
    """
    Parse a workout date from SQLite.
    SQLAlchemy 2 + SQLite returns strings like "2025-03-14 09:30:00.000000".
    Python 3.11 fromisoformat handles this directly.
    """
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    return datetime.fromisoformat(str(raw)).date()


def _build_daily_vl(rows: list[dict]) -> pd.Series:
    """
    Aggregate raw SQL rows into a contiguous daily VL Series.

    - Groups rows by workout_id → computes VL per workout
    - Multiple workouts on the same calendar day are summed
    - Rest-day workouts contribute 0 VL
    - Missing days between first and last date are 0-filled

    Returns a pd.Series indexed by DatetimeIndex (daily freq), sorted ascending.
    Returns an empty Series if rows is empty.
    """
    if not rows:
        return pd.Series(dtype=float)

    # Group rows by workout_id; also capture per-workout metadata
    workout_groups: dict[int, list[dict]] = defaultdict(list)
    workout_meta: dict[int, dict] = {}

    for row in rows:
        wid = row["workout_id"]
        workout_groups[wid].append(row)
        if wid not in workout_meta:
            workout_meta[wid] = {
                "date": row["workout_date"],
                "is_rest_day": bool(row["is_rest_day"]),
            }

    # Compute VL per date, summing across multiple workouts on the same day
    daily_vl: dict[date, float] = {}
    for wid, group_rows in workout_groups.items():
        meta = workout_meta[wid]
        workout_date = _parse_workout_date(meta["date"])
        vl = 0.0 if meta["is_rest_day"] else _compute_workout_vl(group_rows)
        daily_vl[workout_date] = daily_vl.get(workout_date, 0.0) + vl

    if not daily_vl:
        return pd.Series(dtype=float)

    # Build a contiguous date range; 0-fill gaps (unlogged days = no training)
    all_dates = sorted(daily_vl.keys())
    idx = pd.date_range(start=all_dates[0], end=all_dates[-1], freq="D")
    series = pd.Series(
        {pd.Timestamp(d): v for d, v in daily_vl.items()}
    ).reindex(idx, fill_value=0.0)

    return series.sort_index()


# ---------------------------------------------------------------------------
# ACWR metrics
# ---------------------------------------------------------------------------


def _zone_and_label(acwr: float) -> tuple[str, str]:
    if acwr < 0.8:
        return "undertrained", "Training load is below optimal"
    if acwr <= 1.3:
        return "optimal", "Training load is optimal"
    if acwr <= 1.5:
        return "caution", "Training load is elevated"
    return "high_risk", "Training load is high — reduce intensity"


def _compute_metrics(daily_vl: pd.Series) -> dict:
    """
    Compute ACWR and derived metrics from a contiguous daily VL Series.

    EWMA uses adjust=False (recursive formula) to match the λ definition
    in ML_FEATURES.md. This differs from pandas' default adjust=True.
    """
    acute_series = daily_vl.ewm(span=7, adjust=False).mean()
    chronic_series = daily_vl.ewm(span=28, adjust=False).mean()

    acute_load = float(acute_series.iloc[-1])
    chronic_load = float(chronic_series.iloc[-1])
    acwr = acute_load / chronic_load if chronic_load > 0 else 0.0

    # Monotony over the last 7 days (or all days if fewer than 7)
    last_7 = daily_vl.iloc[-7:] if len(daily_vl) >= 7 else daily_vl
    mean_7 = float(last_7.mean())
    std_7 = float(last_7.std(ddof=1)) if len(last_7) > 1 else 0.0
    monotony = mean_7 / std_7 if std_7 > 0 else 0.0

    weekly_vl = float(last_7.sum())
    strain = weekly_vl * monotony

    zone, readiness_label = _zone_and_label(acwr)

    return {
        "acwr": round(acwr, 4),
        "acwr_zone": zone,
        "acute_load": round(acute_load, 2),
        "chronic_load": round(chronic_load, 2),
        "monotony": round(monotony, 4),
        "strain": round(strain, 2),
        "readiness_label": readiness_label,
    }


# ---------------------------------------------------------------------------
# Cold start guard
# ---------------------------------------------------------------------------


def _cold_start(days: int) -> tuple[bool, dict | None, str | None]:
    """
    Check data sufficiency.

    Returns:
        (is_hard_error, error_payload, warning_string)
        - is_hard_error=True  → caller should return error_payload immediately
        - warning_string      → non-None when 7 ≤ days < 28
    """
    if days < _MIN_DAYS_HARD:
        return True, {
            "error": "insufficient_data",
            "message": "At least 7 days of workout data required.",
            "minimum_required": _MIN_DAYS_HARD,
            "current_days": days,
        }, None

    warning = None
    if days < _MIN_DAYS_WARN:
        warning = (
            f"ACWR requires 28 days of data for full accuracy "
            f"— currently {days} days in"
        )

    return False, None, warning


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/status")
def fatigue_status(user_id: int = Query(...)):
    """
    GET /api/ml/fatigue/status?user_id={int}

    Returns the current ACWR, zone classification, acute/chronic loads,
    monotony, and strain. Cached for 24 hours per user; invalidate via
    POST /api/ml/fatigue/invalidate after a new workout is logged.
    """
    cached = _cache_get(user_id)
    if cached:
        return JSONResponse(content=cached)

    rows = _fetch_raw_rows(user_id)
    daily_vl = _build_daily_vl(rows)
    days_of_data = len(daily_vl)

    is_error, error_payload, warning = _cold_start(days_of_data)
    if is_error:
        return JSONResponse(status_code=422, content=error_payload)

    metrics = _compute_metrics(daily_vl)
    payload = {**metrics, "days_of_data": days_of_data, "warning": warning}

    _cache_set(user_id, payload)
    return JSONResponse(content=payload)


@router.get("/history")
def fatigue_history(user_id: int = Query(...), days: int = Query(default=28)):
    """
    GET /api/ml/fatigue/history?user_id={int}&days={int}

    Returns time-series arrays for ACWR, acute load, chronic load, and raw
    volume load over the requested window.

    IMPORTANT: EWMA is always computed on the FULL historical series before
    slicing to the requested window. Slicing before computing would produce
    incorrect exponential weights because prior context would be lost.
    """
    rows = _fetch_raw_rows(user_id)
    daily_vl = _build_daily_vl(rows)
    days_of_data = len(daily_vl)

    is_error, error_payload, _ = _cold_start(days_of_data)
    if is_error:
        return JSONResponse(status_code=422, content=error_payload)

    # Compute EWMA on full series, then slice — never the other way around
    full_acute = daily_vl.ewm(span=7, adjust=False).mean()
    full_chronic = daily_vl.ewm(span=28, adjust=False).mean()

    window = daily_vl.iloc[-days:]
    acute_window = full_acute.iloc[-days:]
    chronic_window = full_chronic.iloc[-days:]

    return JSONResponse(content=format_history_payload(window, acute_window, chronic_window))


class _InvalidateRequest(BaseModel):
    user_id: int


@router.post("/invalidate")
def fatigue_invalidate(body: _InvalidateRequest):
    """
    POST /api/ml/fatigue/invalidate
    Body: { "user_id": int }

    Clears the cached status for a user. Call this from the main app
    whenever a new workout is saved for that user.
    """
    _cache_invalidate(body.user_id)
    return {"invalidated": True, "user_id": body.user_id}
