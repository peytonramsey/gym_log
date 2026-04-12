"""
Bayesian 1RM Estimator using PyMC.

Models the user's true 1-rep max as a latent Normal variable.
Each logged set is treated as a noisy Epley-formula reading of that latent:
    1RM_estimated = weight × (1 + reps / 30)

Output is the 94% Highest Density Interval (HDI), not a point estimate.
The interval IS the result — it must always be shown in the UI.

Stack: pymc, arviz

Tracked movements (compound only):
    Back Squat, Conventional Deadlift, Bench Press (Flat Barbell),
    Overhead Press (Standing Barbell), Romanian Deadlift, Barbell Row
"""

import json
import os

import arviz as az
import numpy as np
import pymc as pm
from dotenv import load_dotenv
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from bayesian.cache import get_cached_trace, invalidate, set_cached_trace

load_dotenv()

router = APIRouter()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///c:/Users/ramse/gymlog/instance/gymlog.db",
)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ---------------------------------------------------------------------------
# Movement configuration
# ---------------------------------------------------------------------------

# URL slug → canonical DB name
MOVEMENT_MAP: dict[str, str] = {
    "back-squat":            "Back Squat",
    "conventional-deadlift": "Conventional Deadlift",
    "bench-press":           "Bench Press (Flat Barbell)",
    "overhead-press":        "Overhead Press (Standing Barbell)",
    "romanian-deadlift":     "Romanian Deadlift",
    "barbell-row":           "Barbell Row",
}

# Canonical DB name → known name variants (handles legacy un-normalized data)
MOVEMENT_ALIASES: dict[str, list[str]] = {
    "Back Squat": [
        "Back Squat", "Back Squats", "Squat", "Squats",
    ],
    "Conventional Deadlift": [
        "Conventional Deadlift", "Deadlift", "Deadlifts",
    ],
    "Bench Press (Flat Barbell)": [
        "Bench Press (Flat Barbell)", "Bench Press",
    ],
    "Overhead Press (Standing Barbell)": [
        "Overhead Press (Standing Barbell)", "Overhead Press", "OHP", "Shoulder Press",
    ],
    "Romanian Deadlift": [
        "Romanian Deadlift", "Romanian Deadlifts", "RDL",
    ],
    "Barbell Row": [
        "Barbell Row", "Barbell Rows", "Rows", "BB Row",
    ],
}

# ---------------------------------------------------------------------------
# Epley formula
# ---------------------------------------------------------------------------

def epley(weight: float, reps: int) -> float:
    """Epley 1RM estimate: weight × (1 + reps/30). Returns weight exactly at reps=1."""
    return weight * (1.0 + reps / 30.0)


# ---------------------------------------------------------------------------
# Database fetch
# ---------------------------------------------------------------------------

def _fetch_sets(user_id: int, movement_name: str) -> tuple[list[tuple[float, int]], int]:
    """Fetch all completed sets for a user and movement.

    Returns:
        (observed_sets, n_sessions) where:
          - observed_sets: list of (weight, reps) tuples ordered chronologically
          - n_sessions: count of unique workout dates (used for uncertainty note)

    Parses set_data JSON preferentially; falls back to top-level
    (sets, reps, weight) columns when set_data is absent or unparseable.
    The `completed` field in set_data defaults to True when absent.
    Only includes sets where reps > 0 and weight > 0.
    """
    aliases = MOVEMENT_ALIASES.get(movement_name, [movement_name])
    bind_keys = {f"name{i}": alias for i, alias in enumerate(aliases)}
    in_clause = ", ".join(f":name{i}" for i in range(len(aliases)))

    query = text(f"""
        SELECT
            w.date        AS workout_date,
            e.sets,
            e.reps,
            e.weight,
            e.set_data
        FROM exercise e
        JOIN workout w ON e.workout_id = w.id
        WHERE w.user_id = :user_id
          AND e.name IN ({in_clause})
          AND w.is_draft = 0
        ORDER BY w.date ASC
    """)

    params = {"user_id": user_id, **bind_keys}

    observed: list[tuple[float, int]] = []
    workout_dates: set[str] = set()

    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()

    for row in rows:
        workout_dates.add(str(row.workout_date)[:10])  # date portion only

        sets_count = row.sets or 1
        reps_top = row.reps or 0
        weight_top = row.weight

        if row.set_data:
            try:
                sets_json = json.loads(row.set_data)
                parsed_any = False
                for s in sets_json:
                    w = s.get("weight")
                    r = s.get("reps", 0) or 0
                    completed = s.get("completed", True)  # absent → True (legacy)
                    if w and w > 0 and r > 0 and completed:
                        observed.append((float(w), int(r)))
                        parsed_any = True
                if parsed_any:
                    continue  # set_data took precedence; skip top-level fallback
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass  # fall through to top-level fields

        # Fallback: top-level fields — expand sets_count identical sets
        if weight_top and weight_top > 0 and reps_top > 0:
            for _ in range(sets_count):
                observed.append((float(weight_top), int(reps_top)))

    return observed, len(workout_dates)


# ---------------------------------------------------------------------------
# PyMC model
# ---------------------------------------------------------------------------

def _run_model(observed_sets: list[tuple[float, int]]) -> tuple:
    """Fit the Bayesian 1RM model and return (trace, hdi_lower, hdi_upper, posterior_mean).

    Prior is anchored at the Epley estimate of the first (chronologically earliest) set.
    sigma prior = 15% of prior mean, reflecting expected variation in Epley readings.

    Returns: (trace, hdi_lower, hdi_upper, posterior_mean)
    """
    first_weight, first_reps = observed_sets[0]
    mu_prior = epley(first_weight, first_reps)
    epley_vals = np.array([epley(w, r) for w, r in observed_sets])

    with pm.Model():
        one_rm = pm.Normal("one_rm", mu=mu_prior, sigma=mu_prior * 0.15)
        sigma = pm.HalfNormal("sigma", sigma=10)
        pm.Normal("obs", mu=one_rm, sigma=sigma, observed=epley_vals)
        trace = pm.sample(
            1000,
            tune=500,
            progressbar=False,
            chains=2,
            discard_tuned_samples=True,
        )

    hdi_result = az.hdi(trace, hdi_prob=0.94)
    hdi_lower = float(hdi_result["one_rm"].values[0])
    hdi_upper = float(hdi_result["one_rm"].values[1])
    posterior_mean = float(trace.posterior["one_rm"].values.mean())

    return trace, hdi_lower, hdi_upper, posterior_mean


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/1rm/{movement}")
def get_1rm(movement: str, user_id: int = Query(...)):
    """GET /api/ml/bayesian/1rm/{movement}?user_id={int}

    Returns the 94% HDI credible interval for the user's estimated 1RM.
    Results are cached in-process until invalidated by POST /1rm/update.

    movement: URL slug (e.g. "back-squat", "bench-press")
    """
    movement_name = MOVEMENT_MAP.get(movement)
    if movement_name is None:
        return JSONResponse(
            status_code=404,
            content={"error": "unknown_movement", "message": f"Unknown movement: {movement}"},
        )

    # Cache hit — re-extract HDI from stored trace (microseconds)
    cached = get_cached_trace(user_id, movement_name)
    if cached is not None:
        trace = cached["trace"]
        n_sessions = cached["n_sessions"]
        last_updated = cached["last_updated"]

        hdi_result = az.hdi(trace, hdi_prob=0.94)
        hdi_lower = float(hdi_result["one_rm"].values[0])
        hdi_upper = float(hdi_result["one_rm"].values[1])
        posterior_mean = float(trace.posterior["one_rm"].values.mean())

        uncertainty_note = (
            f"Wide interval — only {n_sessions} logged sessions" if n_sessions < 6 else None
        )

        return JSONResponse(content={
            "movement":         movement_name,
            "posterior_mean":   round(posterior_mean, 1),
            "hdi_lower":        round(hdi_lower, 1),
            "hdi_upper":        round(hdi_upper, 1),
            "hdi_probability":  0.94,
            "n_observations":   n_sessions,
            "last_updated":     last_updated,
            "uncertainty_note": uncertainty_note,
        })

    # Cache miss — fetch from DB and run PyMC
    observed_sets, n_sessions = _fetch_sets(user_id, movement_name)

    if not observed_sets:
        return JSONResponse(
            status_code=422,
            content={
                "error":    "insufficient_data",
                "message":  f"No logged sets found for {movement_name}",
                "movement": movement_name,
            },
        )

    trace, hdi_lower, hdi_upper, posterior_mean = _run_model(observed_sets)
    set_cached_trace(user_id, movement_name, trace, n_sessions)

    last_updated = get_cached_trace(user_id, movement_name)["last_updated"]
    uncertainty_note = (
        f"Wide interval — only {n_sessions} logged sessions" if n_sessions < 6 else None
    )

    return JSONResponse(content={
        "movement":         movement_name,
        "posterior_mean":   round(posterior_mean, 1),
        "hdi_lower":        round(hdi_lower, 1),
        "hdi_upper":        round(hdi_upper, 1),
        "hdi_probability":  0.94,
        "n_observations":   n_sessions,
        "last_updated":     last_updated,
        "uncertainty_note": uncertainty_note,
    })


class _UpdateRequest(BaseModel):
    movement: str   # URL slug or canonical name — both handled
    weight: float = 0.0
    reps: int = 0
    user_id: int


@router.post("/1rm/update")
def update_1rm(body: _UpdateRequest):
    """POST /api/ml/bayesian/1rm/update

    Invalidates the cached trace for (user_id, movement) so the next GET
    re-samples from the updated dataset. Lazy evaluation — does not run
    the model itself.

    movement accepts either a URL slug ("bench-press") or canonical name.
    """
    movement_name = MOVEMENT_MAP.get(body.movement, body.movement)
    invalidate(body.user_id, movement_name)
    return {"updated": True}
