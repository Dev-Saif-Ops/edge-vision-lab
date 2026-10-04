"""The function under test: how long to wait before retry number `attempt` (0-based)."""

import random


def retry_delay(
    attempt: int, initial: float = 0.5, cap: float = 30.0, rng: random.Random | None = None
) -> float:
    """Exponential backoff with equal jitter: a random wait between half and all of
    min(initial * 2**attempt, cap)."""
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    ceiling = min(initial * 2**attempt, cap)
    return (rng or random).uniform(ceiling / 2, ceiling)
