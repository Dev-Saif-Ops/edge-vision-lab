"""Can several threads open video streams at the same time? A fake says yes. OpenCV says no.

Three threads each open a stream to an address that never answers (10.255.255.1, a
non-routable address), with a 2-second open timeout.

  fake capture   a stand-in that sleeps 2 s per open, like a test double would
  real OpenCV    cv2.VideoCapture with the FFmpeg backend

If opens run in parallel, all three finish at ~2 s. If they are serialised, they finish at
~2, ~4 and ~6 s.

Run:  uv run python 04-test-doubles/serialised_opens.py   (needs no camera; takes ~10 s)
"""

import os
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("OPENCV_FFMPEG_LOGLEVEL", "-8")  # keep FFmpeg quiet
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import plt, save, style

DEAD = "rtsp://10.255.255.1:554/stream"
TIMEOUT_MS = 2000


class FakeCapture:
    """What a unit test might use instead of OpenCV: same duration, no shared state."""

    def __init__(self, uri: str, *_: object) -> None:
        time.sleep(TIMEOUT_MS / 1000)

    def isOpened(self) -> bool:
        return False


def real_capture(uri: str) -> object:
    return cv2.VideoCapture(uri, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, TIMEOUT_MS])


def finish_times(open_fn) -> list[float]:  # type: ignore[no-untyped-def]
    done: list[float] = []
    lock = threading.Lock()
    start = time.monotonic()

    def worker() -> None:
        open_fn(DEAD)
        with lock:
            done.append(time.monotonic() - start)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(done)


if __name__ == "__main__":
    fake = finish_times(FakeCapture)
    real = finish_times(real_capture)
    print("three parallel opens to a dead stream, 2 s timeout each\n")
    print(f"  fake capture: finished at {', '.join(f'{t:.1f}' for t in fake)} s   (parallel)")
    print(
        f"  real OpenCV:  finished at {', '.join(f'{t:.1f}' for t in real)} s   "
        f"({'serialised' if real[-1] > 1.5 * real[0] else 'parallel'})"
    )
    print(f"\nOpenCV {cv2.__version__}. A test built on the fake would 'prove' parallel opens.")

    fig, ax = plt.subplots()
    rows = [("fake capture", fake), ("real OpenCV", real)]
    for row, (_name, times) in enumerate(rows):
        for i, t in enumerate(times):  # one lane per open, so overlapping bars stay visible
            y = row * 4 + i
            ax.barh(y, TIMEOUT_MS / 1000, left=t - TIMEOUT_MS / 1000, height=0.7, color=f"C{row}")
            ax.text(t + 0.05, y, f"open {i + 1} done at {t:.1f} s", va="center", fontsize=11)
    ax.set_yticks([1, 5], [name for name, _ in rows], fontsize=13)
    ax.invert_yaxis()
    style(ax, "Same test, different truth: three parallel stream opens", "seconds", "")
    print(f"chart: {save(fig, '04-test-doubles')}")
