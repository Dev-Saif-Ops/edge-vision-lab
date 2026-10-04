"""A camera produces 60 frames/s. Your model handles 10 frames/s. What happens?

Two designs:
  queue        keep every frame, process them in order
  newest-only  keep one slot; the camera overwrites it, the consumer takes whatever is newest

Run:  uv run python 01-newest-frame/newest_frame.py          (simulation + chart)
      uv run python 01-newest-frame/newest_frame.py --live   (real threads, 5 seconds)
"""

import argparse
import sys
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import plt, save, style

CAMERA_FPS = 60
CONSUMER_FPS = 10
FRAME_BYTES = 832 * 464 * 3  # one 832x464 colour frame = 1.16 MB


def simulate(seconds: int = 60) -> list[dict[str, float]]:
    """Step through time in camera ticks and record what each design looks like."""
    rows = []
    queue: deque[float] = deque()  # capture times of frames waiting in the queue
    newest: float | None = None
    next_consume = 0.0
    queue_lag = newest_lag = 0.0
    dt = 1 / CAMERA_FPS
    for i in range(seconds * CAMERA_FPS + 1):
        now = i * dt
        queue.append(now)  # camera produces a frame
        newest = now
        if now >= next_consume:  # consumer is free: take a frame
            queue_lag = now - queue.popleft()  # oldest waiting frame
            newest_lag = now - newest  # always the latest
            next_consume += 1 / CONSUMER_FPS
        if i % CAMERA_FPS == 0:
            rows.append(
                {
                    "t": now,
                    "queue_frames": len(queue),
                    "queue_mb": len(queue) * FRAME_BYTES / 1e6,
                    "queue_lag": queue_lag,
                    "newest_mb": FRAME_BYTES / 1e6,
                    "newest_lag": newest_lag,
                }
            )
    return rows


def report(rows: list[dict[str, float]]) -> None:
    print(f"camera {CAMERA_FPS} fps, consumer {CONSUMER_FPS} fps, frame {FRAME_BYTES / 1e6:.2f} MB\n")
    print(
        f"{'t (s)':>6} | {'queue: frames':>13} {'memory':>10} {'lag':>8} | "
        f"{'newest-only: memory':>19} {'lag':>8}"
    )
    print("-" * 78)
    for r in rows:
        if int(r["t"]) in (1, 5, 10, 30, 60):
            print(
                f"{r['t']:6.0f} | {r['queue_frames']:13.0f} {r['queue_mb'] / 1000:8.2f} GB "
                f"{r['queue_lag']:7.1f}s | {r['newest_mb']:16.2f} MB {r['newest_lag'] * 1000:6.0f}ms"
            )
    last = rows[-1]
    wait = last["queue_frames"] / CONSUMER_FPS
    print(f"\nAfter 60 s a frame arriving now waits {wait:.0f} s ({wait / 60:.0f} min) in the queue.")


def chart(rows: list[dict[str, float]]) -> Path:
    t = [r["t"] for r in rows]
    fig, (a, b) = plt.subplots(1, 2)
    a.plot(t, [r["queue_mb"] / 1000 for r in rows], lw=3, label="queue every frame")
    a.plot(t, [r["newest_mb"] / 1000 for r in rows], lw=3, label="keep newest only")
    style(a, "Memory", "seconds", "GB")
    a.legend(fontsize=12)
    b.plot(t, [r["queue_lag"] for r in rows], lw=3, label="queue every frame")
    b.plot(t, [r["newest_lag"] for r in rows], lw=3, label="keep newest only")
    style(b, "Age of the frame being processed", "seconds", "lag (s)")
    b.legend(fontsize=12)
    fig.suptitle("Camera 60 fps, model 10 fps", fontsize=14, x=0.01, ha="left")
    return save(fig, "01-newest-frame")


def live(seconds: float = 5.0) -> None:
    """The same thing with real threads and real arrays, so you can watch memory grow."""
    frame = np.zeros((464, 832, 3), np.uint8)
    queue: deque[np.ndarray] = deque()
    slot: list[np.ndarray] = []
    lock = threading.Lock()
    stop = threading.Event()

    def camera() -> None:
        while not stop.is_set():
            f = frame.copy()
            with lock:
                queue.append(f)
                slot[:] = [f]
            time.sleep(1 / CAMERA_FPS)

    threading.Thread(target=camera, daemon=True).start()
    start = time.monotonic()
    print(f"{'t':>4} {'queue length':>13} {'queue memory':>13}  newest-only memory")
    while (elapsed := time.monotonic() - start) < seconds:
        time.sleep(1 / CONSUMER_FPS)  # "inference"
        with lock:
            if queue:
                queue.popleft()
            n = len(queue)
        if abs(elapsed - round(elapsed)) < 0.05:
            print(f"{elapsed:4.0f} {n:13d} {n * FRAME_BYTES / 1e6:10.0f} MB  {FRAME_BYTES / 1e6:.2f} MB")
    stop.set()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="run real threads for 5 seconds")
    args = parser.parse_args()
    if args.live:
        live()
    else:
        rows = simulate()
        report(rows)
        print(f"chart: {chart(rows)}")
