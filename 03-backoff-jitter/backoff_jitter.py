"""200 devices lose their server at the same moment (a switch reboots). The server is back
after 20 s. How hard do the devices hit it, and how long until everyone is reconnected?

Strategies (cap 30 s):
  fixed           retry every 1 s
  exponential     1, 2, 4, 8 ... s, no randomness
  full jitter     uniform(0, delay)
  equal jitter    uniform(delay/2, delay)

Run:  uv run python 03-backoff-jitter/backoff_jitter.py
"""

import random
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import plt, save, style

DEVICES, SERVER_BACK_AT, INITIAL, CAP, BUCKET = 200, 20.0, 1.0, 30.0, 0.5

Strategy = Callable[[float, random.Random], float]
STRATEGIES: dict[str, Strategy] = {
    "fixed 1 s": lambda d, r: INITIAL,
    "exponential": lambda d, r: d,
    "full jitter": lambda d, r: r.uniform(0, d),
    "equal jitter": lambda d, r: r.uniform(d / 2, d),
}


def run(wait: Strategy, seed: int = 7) -> tuple[Counter[float], float]:
    """Return RETRY attempts per time bucket (the failure at t=0 itself is the same for every
    strategy, so it isn't counted), and when the last device reconnected."""
    rng = random.Random(seed)
    retries: Counter[float] = Counter()
    last_connected = 0.0
    for _ in range(DEVICES):
        t, delay = wait(INITIAL, rng), INITIAL  # first retry after the initial failure
        while True:
            retries[round(t // BUCKET * BUCKET, 2)] += 1
            if t >= SERVER_BACK_AT:
                last_connected = max(last_connected, t)
                break
            delay = min(delay * 2, CAP)
            t += wait(delay, rng)
    return retries, last_connected


def peak_after_recovery(retries: Counter[float]) -> int:
    """The worst 0.5 s the server sees once it is back up: the thundering-herd moment.
    (Without jitter, everyone arrives together, whenever that is.)"""
    return max((n for t, n in retries.items() if t >= SERVER_BACK_AT), default=0)


if __name__ == "__main__":
    print(f"{DEVICES} devices, server back after {SERVER_BACK_AT:.0f} s, backoff cap {CAP:.0f} s\n")
    print(
        f"{'strategy':<14} {'retries':>8} {'peak / 0.5 s':>13} {'peak once server is back':>25} "
        f"{'all back after':>15}"
    )
    fig, ax = plt.subplots()
    results = {}
    for name, wait in STRATEGIES.items():
        retries, done = run(wait)
        results[name] = retries
        print(
            f"{name:<14} {sum(retries.values()):8d} {max(retries.values()):13d} "
            f"{peak_after_recovery(retries):25d} {done:13.1f} s"
        )
    # Chart every bucket, including the empty ones: without jitter the shape IS the silence
    # between synchronized spikes. "fixed" stays in the table but would flood the chart.
    grid = [round(k * BUCKET, 2) for k in range(int(52 / BUCKET))]
    for name in ("exponential", "full jitter", "equal jitter"):
        ax.step(grid, [results[name].get(x, 0) for x in grid], where="post", lw=2.5, label=name)
    ax.axvline(SERVER_BACK_AT, color="black", ls="--", lw=1)
    ax.text(SERVER_BACK_AT + 0.3, ax.get_ylim()[1] * 0.9, "server back", fontsize=12)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=0, top=300)
    style(
        ax,
        "200 devices retrying after an outage (no jitter = synchronized spikes)",
        "seconds",
        "retries per 0.5 s",
    )
    ax.legend(fontsize=12)
    print(f"\nchart: {save(fig, '03-backoff-jitter')}")
    print("\nFixed retries hammer the server the whole time. Exponential backoff without jitter")
    print("retries less, but all 200 devices stay in lock-step and hit the recovering server in the")
    print("same instant. Jitter spreads them out, at a price: the last device reconnects later.")
    print("That trade-off (smaller spikes vs slower full recovery) is the real decision.")
