"""Tests that look fine, reach 100% line coverage, and catch almost nothing."""

from backoff import retry_delay


def test_returns_a_positive_number() -> None:
    assert retry_delay(0) > 0


def test_later_attempts_can_wait_longer() -> None:
    assert retry_delay(5) > 0
