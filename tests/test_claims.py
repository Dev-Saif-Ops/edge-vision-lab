"""Every headline number in the READMEs, checked. If an experiment changes, these fail first."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(Path(path).stem, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((ROOT / path).parent))
    spec.loader.exec_module(module)
    return module


def test_queue_grows_to_3_5_gb_and_a_5_minute_wait() -> None:
    m = load("01-newest-frame/newest_frame.py")
    last = m.simulate(60)[-1]
    assert 3.4 < last["queue_mb"] / 1000 < 3.6
    assert 49 < last["queue_lag"] < 51
    assert round(last["queue_frames"] / m.CONSUMER_FPS / 60) == 5
    assert last["newest_mb"] < 1.2


def test_smoothed_rate_stays_high_while_window_count_drops_to_zero() -> None:
    m = load("02-rate-metrics/rate_metrics.py")
    times, at = m.arrivals(), [5.0, 7.5]
    assert all(v > 900 for v in m.smoothed_inverse_gap(times, at))
    assert m.window_count(times, at) == [0.0, 0.0]


def test_jitter_shrinks_the_recovery_spike_but_slows_full_recovery() -> None:
    m = load("03-backoff-jitter/backoff_jitter.py")
    exp, exp_done = m.run(m.STRATEGIES["exponential"])
    full, full_done = m.run(m.STRATEGIES["full jitter"])
    eq, _ = m.run(m.STRATEGIES["equal jitter"])
    assert m.peak_after_recovery(exp) == 200
    assert m.peak_after_recovery(full) <= 20
    assert m.peak_after_recovery(eq) <= 20
    assert full_done > exp_done


def test_mutation_tool_skips_docstrings_and_scores_as_claimed() -> None:
    m = load("05-mutation-testing/mutate.py")
    mutated = m.mutate(m.SOURCE, "min(initial * 2**attempt, cap)", "initial * 2**attempt")
    assert "ceiling = initial * 2**attempt\n" in mutated  # the code changed...
    assert "min(initial * 2**attempt, cap)." in mutated  # ...and the docstring did not
    weak = sum(not m.survives("test_weak.py", m.mutate(m.SOURCE, o, n)) for _, o, n in m.MUTANTS)
    strong = sum(not m.survives("test_strong.py", m.mutate(m.SOURCE, o, n)) for _, o, n in m.MUTANTS)
    assert (weak, strong) == (0, len(m.MUTANTS))


def test_three_redactors_leak_12_5_and_0_of_17() -> None:
    m = load("06-url-redaction/redaction.py")
    assert len(m.URLS) == 17
    assert len(m.leaks(m.block_list)) == 12
    assert len(m.leaks(m.path_keeping_allow_list)) == 5
    assert m.leaks(m.shortest_allow_list) == []
    # the path-keeping version's leaks are exactly the five "harmless-looking path" URLs
    assert m.leaks(m.path_keeping_allow_list) == [u for u, _, _ in m.URLS[12:]]


def test_dropping_at_the_source_is_far_cheaper_than_dropping_late() -> None:
    m = load("08-drop-at-source/drop_at_source.py")
    rows = m.run()
    ms = [r[1] for r in rows]
    assert [r[2] for r in rows] == [10, 10, 10, 10]  # the model gets the same frames every way
    assert ms[0] > ms[1] > ms[2] > ms[3]  # decode all > grab-only > 10 fps > 10 fps small
    assert ms[0] / ms[3] > 5  # README says ~10x; timing varies by machine, so a safe floor
    assert abs(rows[3][3] - rows[0][3] / 4) < 1e-9  # half width and height: a quarter of the memory
    memory, disk = m.log_cost(100)
    assert disk > 100 * memory  # a flushed disk write per frame is orders of magnitude slower
