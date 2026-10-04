"""Tests written by asking "what bug would get past this?" for every line."""

import random

import pytest
from backoff import retry_delay


@pytest.mark.parametrize(("attempt", "ceiling"), [(0, 0.5), (1, 1.0), (3, 4.0), (6, 30.0), (20, 30.0)])
def test_stays_between_half_and_all_of_the_capped_ceiling(attempt: int, ceiling: float) -> None:
    rng = random.Random(1)
    for _ in range(200):
        assert ceiling / 2 <= retry_delay(attempt, rng=rng) <= ceiling


def test_actually_uses_the_whole_jitter_range() -> None:
    rng = random.Random(1)
    waits = [retry_delay(2, rng=rng) for _ in range(500)]  # ceiling 2.0
    assert min(waits) < 1.1
    assert max(waits) > 1.9


def test_rejects_negative_attempts() -> None:
    with pytest.raises(ValueError):
        retry_delay(-1)
