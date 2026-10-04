# Keep the newest frame, not every frame

A camera at 60 fps, a model at 10 fps. Queue every frame and memory and lag grow without limit;
keep one "newest frame" slot and both stay flat.

## Run it

```bash
uv run python 01-newest-frame/newest_frame.py
```

## What you'll see

```
 t (s) | queue: frames     memory      lag | newest-only: memory
    10 |           500     0.58 GB     8.3s |             1.16 MB
    60 |          3001     3.48 GB    49.9s |             1.16 MB
After 60 s a frame arriving now waits 300 s (5 min) in the queue.
```
`--live` runs real threads: memory climbs ~50 MB every second.

## The lessons

- In video, being **current** matters more than being **complete**. Dropping frames on purpose is the design, not a bug.
- A queue only works if the consumer is faster than the producer on average. Cameras don't wait.
- Batch processing of a recorded file is the opposite case: there you want every frame, in order.

## For a post

**Screenshot:** `out/01-newest-frame.png` (memory and lag side by side) and the terminal table.

**Hook:** "My camera code throws away 85% of frames. On purpose."
1. 60 fps in, 10 fps out: a queue grows 50 frames/s → 3.5 GB and a 5-minute wait after one minute.
2. One slot holding the newest frame: 1.16 MB forever, lag of one frame.
3. When you *do* want every frame (offline files), and why it's a different mode.
**Ask:** "Where else have you seen 'drop on purpose' beat 'process everything'?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
