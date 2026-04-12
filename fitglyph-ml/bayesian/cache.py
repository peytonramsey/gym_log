"""
Trace cache for Bayesian 1RM model.

Caches PyMC trace objects per (user_id, movement) pair to avoid
re-sampling from scratch on every request. Cache is invalidated
when a new set is logged for the relevant movement.

Cache is in-process and in-memory. Traces are kept forever until
explicitly invalidated — there is no TTL because sampling is expensive
and 1RM changes slowly. The POST /1rm/update endpoint triggers
invalidation after a new workout is logged.

Cache key: (user_id: int, movement: str) where movement is the canonical
DB name (e.g. "Back Squat"), not the URL slug.
"""

from datetime import datetime, timezone

# Key: (user_id: int, movement: str)
# Value: {"trace": InferenceData, "n_sessions": int, "last_updated": str (ISO8601 UTC)}
_cache: dict[tuple[int, str], dict] = {}


def get_cached_trace(user_id: int, movement: str) -> dict | None:
    """Return the cached entry for (user_id, movement), or None if not cached.

    Entry shape: {"trace": InferenceData, "n_sessions": int, "last_updated": str}
    """
    return _cache.get((user_id, movement))


def set_cached_trace(
    user_id: int,
    movement: str,
    trace,
    n_sessions: int,
) -> None:
    """Store a PyMC trace in the cache alongside metadata.

    Args:
        user_id:   Flask user ID
        movement:  Canonical exercise name (e.g. "Back Squat")
        trace:     arviz.InferenceData from pm.sample()
        n_sessions: Number of unique workout dates used to fit the model
    """
    _cache[(user_id, movement)] = {
        "trace": trace,
        "n_sessions": n_sessions,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def invalidate(user_id: int, movement: str) -> None:
    """Remove the cached trace for (user_id, movement).

    Safe to call when no entry exists — pops silently.
    """
    _cache.pop((user_id, movement), None)
