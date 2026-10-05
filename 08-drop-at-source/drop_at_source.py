"""Dropping frames late still costs you the work. Drop them at the source.

A camera sends 60 fps; the model needs 10. Experiment 01 kept only the newest frame, which
fixed memory. But every one of the 60 frames was still decoded (unzipped) and colour-converted
before 50 were thrown away. Video frames depend on each other (most of them only describe what
changed since the previous one), so the decoder can't simply skip them. The real fix is to ask
the camera for less: 10 fps, and a smaller picture.

Four ways to get 10 frames a second out of the same synthetic scene, timed on this machine:

  decode all 60, keep 10    read() every frame, drop 50 afterwards
  grab 60, convert 10       grab() every frame (still decoded), retrieve() only the 10 we keep
  camera sends 10 fps       the stream itself has 10 fps
  camera sends 10 fps, small   10 fps at half width and height

Part 2 times the other trap: writing one log line per frame to disk, flushed each time.

Run:  uv run python 08-drop-at-source/drop_at_source.py
"""

import fcntl
import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import plt, save, style

SECONDS = 5
CAMERA_FPS, MODEL_FPS = 60, 10
FULL, SMALL = (1280, 720), (640, 360)


def scene(t: float, size: tuple[int, int]) -> np.ndarray:
    """A moving, slightly noisy picture, so the encoder has real work to do."""
    w, h = size
    x = np.linspace(0, 1, w, dtype=np.float32)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    base = (np.sin(8 * x + 3 * t) + np.cos(6 * y - 2 * t)) * 60 + 128
    img = np.dstack([base, np.roll(base, w // 3, axis=1), base[::-1]]).astype(np.uint8)
    cx, cy = int(w * (0.5 + 0.4 * np.sin(t))), int(h * (0.5 + 0.3 * np.cos(1.3 * t)))
    cv2.circle(img, (cx, cy), h // 8, (255, 255, 255), -1)
    rng = np.random.default_rng(int(t * 1000))
    return cv2.add(img, rng.integers(0, 12, img.shape, dtype=np.uint8))


def make_clip(path: Path, fps: int, size: tuple[int, int]) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    assert writer.isOpened(), "OpenCV could not open a video writer"
    for i in range(SECONDS * fps):
        writer.write(scene(i / fps, size))
    writer.release()
    return path


def decode_all_keep_some(path: Path) -> int:
    cap, kept, i = cv2.VideoCapture(str(path)), 0, 0
    while True:
        ok, _ = cap.read()  # decode + convert to BGR, for every frame
        if not ok:
            break
        if i % (CAMERA_FPS // MODEL_FPS) == 0:
            kept += 1  # the model would look at this one
        i += 1  # ...and the other five were decoded for nothing
    cap.release()
    return kept


def grab_all_convert_some(path: Path) -> int:
    cap, kept, i = cv2.VideoCapture(str(path)), 0, 0
    while cap.grab():  # decode only
        if i % (CAMERA_FPS // MODEL_FPS) == 0:
            ok, _ = cap.retrieve()  # convert to BGR only the frames we keep
            kept += ok
        i += 1
    cap.release()
    return kept


def decode_everything(path: Path) -> int:
    cap, kept = cv2.VideoCapture(str(path)), 0
    while cap.read()[0]:
        kept += 1
    cap.release()
    return kept


def timed(fn: Callable[[Path], int], path: Path, repeat: int = 3) -> tuple[float, int]:
    """Best of `repeat` runs, in ms of work per second of video."""
    best, kept = float("inf"), 0
    for _ in range(repeat):
        start = time.perf_counter()
        kept = fn(path)
        best = min(best, time.perf_counter() - start)
    return best * 1000 / SECONDS, kept


def run() -> list[tuple[str, float, int, float]]:
    """(name, ms of work per second of video, frames the model got per second, MB per frame)."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        full60 = make_clip(d / "full60.mp4", CAMERA_FPS, FULL)
        full10 = make_clip(d / "full10.mp4", MODEL_FPS, FULL)
        small10 = make_clip(d / "small10.mp4", MODEL_FPS, SMALL)
        mb_full, mb_small = FULL[0] * FULL[1] * 3 / 1e6, SMALL[0] * SMALL[1] * 3 / 1e6
        rows = []
        for name, fn, path, mb in [
            ("decode all 60, keep 10", decode_all_keep_some, full60, mb_full),
            ("grab 60, convert 10", grab_all_convert_some, full60, mb_full),
            ("camera sends 10 fps", decode_everything, full10, mb_full),
            ("camera sends 10 fps, small", decode_everything, small10, mb_small),
        ]:
            ms, kept = timed(fn, path)
            rows.append((name, ms, kept // SECONDS, mb))
    return rows


def sync_to_disk(fd: int) -> None:
    """Really reach the disk. On macOS plain fsync() stops at the drive's own cache."""
    if hasattr(fcntl, "F_FULLFSYNC"):
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC)
    else:
        os.fsync(fd)


def log_cost(frames: int = 600) -> tuple[float, float]:
    """ms per frame: one log line kept in memory vs written and flushed to disk."""
    lines: list[str] = []
    start = time.perf_counter()
    for i in range(frames):
        lines.append(f"frame {i} processed\n")
    memory = (time.perf_counter() - start) * 1000 / frames
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        start = time.perf_counter()
        for i in range(frames):
            f.write(f"frame {i} processed\n")
            f.flush()
            sync_to_disk(f.fileno())  # what "make sure it's on disk" costs, every frame
        disk = (time.perf_counter() - start) * 1000 / frames
    os.unlink(f.name)
    return memory, disk


def chart(rows: list[tuple[str, float, int, float]]) -> Path:
    fig, ax = plt.subplots()
    names = [r[0] for r in rows]
    ms = [r[1] for r in rows]
    colors = ["#c0392b", "#e67e22", "#27ae60", "#1e8449"]
    bars = ax.barh(names[::-1], ms[::-1], color=colors[::-1])
    for bar, value in zip(bars, ms[::-1], strict=True):
        ax.text(
            bar.get_width(), bar.get_y() + bar.get_height() / 2, f"  {value:.1f} ms", va="center", fontsize=13
        )
    style(
        ax,
        "Same 10 frames/s for the model. Very different work.",
        "Time spent getting frames, per second of video (ms, on a laptop)",
        "",
    )
    ax.set_xlim(0, max(ms) * 1.2)
    ax.tick_params(axis="y", labelsize=14)
    return save(fig, "08-drop-at-source")


if __name__ == "__main__":
    print("Encoding three synthetic clips (a few seconds)...\n")
    rows = run()
    worst = rows[0][1]
    print(f"{'way':<28} {'work per video second':>22} {'model gets':>11} {'per frame':>10}")
    for name, ms, fps, mb in rows:
        print(f"{name:<28} {ms:>14.0f} ms ({ms / worst:4.0%}) {fps:>6} fps {mb:>7.2f} MB")
    memory, disk = log_cost()
    print(
        f"\nOne log line per frame: in memory {memory * 1000:.1f} µs, "
        f"written + flushed to disk {disk:.2f} ms ({disk / memory:,.0f}x slower)"
    )
    print("On an SD card the disk number is far worse than on a laptop SSD.")
    print(f"\nChart: {chart(rows)}")
