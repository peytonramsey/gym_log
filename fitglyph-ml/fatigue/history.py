"""
History formatting helper for the fatigue engine.

Accepts pre-computed EWMA series (from compute.py) and formats them into
the shape returned by GET /api/ml/fatigue/history.

Kept separate from compute.py so the route handler stays focused on math.
"""

import pandas as pd


def format_history_payload(
    window: pd.Series,
    acute_window: pd.Series,
    chronic_window: pd.Series,
) -> dict:
    """
    Format raw VL and EWMA windows into the /history API response shape.

    ACWR is computed per day as acute / chronic. Days where chronic is 0
    (early in a user's history) are set to 0.0 rather than NaN or inf.

    Args:
        window:         Daily VL series for the requested date range.
        acute_window:   7-day EWMA slice matching window's index.
        chronic_window: 28-day EWMA slice matching window's index.

    Returns:
        Dict with keys: dates, volume_load, acute_load, chronic_load, acwr.
    """
    acwr_series = acute_window / chronic_window.replace(0.0, float("nan"))
    acwr_series = acwr_series.fillna(0.0)

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in window.index],
        "volume_load": [round(float(v), 2) for v in window],
        "acute_load": [round(float(v), 2) for v in acute_window],
        "chronic_load": [round(float(v), 2) for v in chronic_window],
        "acwr": [round(float(v), 4) for v in acwr_series],
    }
