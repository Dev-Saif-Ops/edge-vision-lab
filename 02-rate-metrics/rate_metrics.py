"""Two ways to report "frames per second" from frame arrival times, and how one of them lies.

The stream: 60 fps for 3 s, then the connection drops. Just before dying, the decoder flushes
its buffer: 50 frames arrive 1 ms apart. Then nothing for 5 s. Then 60 fps again.

  smoothed 1/gap   ema = 0.9*ema + 0.1*(1/gap), updated on every frame
  window count     number of frames that arrived in the last second

Run:  uv run python 02-rate-metrics/rate_metrics.py
"""

import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import plt, save, style


def arrivals() -> list[float]:
    times = [i / 60 for i in range(180)]  # 0-3 s at 60 fps
    times += [3.0 + i * 0.001 for i in range(1, 51)]  # buffer flush: 50 frames, 1 ms apart
    times += [8.05 + i / 60 for i in range(180)]  # stream returns at ~8 s
    return times


def smoothed_inverse_gap(times: list[float], at: list[float]) -> list[float]:
    """The tempting version: cheap, smooth, and wrong. It only updates when a frame arrives."""
    out, ema, last, i = [], 0.0, None, 0
    for t in at:
        while i < len(times) and times[i] <= t:
            if last is not None and times[i] > last:
                ema = 0.9 * ema + 0.1 / (times[i] - last)
            last = times[i]
            i += 1
        out.append(ema)
    return out


def window_count(times: list[float], at: list[float], window: float = 1.0) -> list[float]:
    """Count arrivals in the last second. A burst adds only the frames it really contains,
    and the value falls to 0 by itself when frames stop."""
    out, recent, i = [], deque(), 0
    for t in at:
        while i < len(times) and times[i] <= t:
            recent.append(times[i])
            i += 1
        while recent and recent[0] < t - window:
            recent.popleft()
        out.append(float(len(recent)))
    return out


if __name__ == "__main__":
    times = arrivals()
    at = [i * 0.05 for i in range(int(11 / 0.05))]
    ema, win = smoothed_inverse_gap(times, at), window_count(times, at)

    print(f"{'t (s)':>6} {'what is happening':<26} {'smoothed 1/gap':>15} {'window count':>13}")
    for t_probe, label in [
        (2, "streaming at 60 fps"),
        (3.1, "buffer flush, then dead"),
        (5, "camera is OFF"),
        (7.5, "camera is OFF"),
        (10, "streaming again"),
    ]:
        k = min(range(len(at)), key=lambda j: abs(at[j] - t_probe))
        print(f"{t_probe:6.1f} {label:<26} {ema[k]:12.0f} fps {win[k]:10.0f} fps")

    fig, ax = plt.subplots()
    ax.plot(at, ema, lw=3, label="smoothed 1/gap (wrong)")
    ax.plot(at, win, lw=3, label="frames in the last second (right)")
    ax.axvspan(3.05, 8.05, color="grey", alpha=0.15, label="camera is off")
    ax.set_yscale("symlog", linthresh=100)
    style(ax, "Measuring fps: the camera is off, the metric says otherwise", "seconds", "reported fps")
    ax.legend(fontsize=12, loc="upper right")
    print(f"\nchart: {save(fig, '02-rate-metrics')}")
