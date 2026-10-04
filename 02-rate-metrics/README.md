# Measure rates with a window, not 1/gap

Two ways to report fps from frame arrival times. The smoothed 1/gap version reports ~1000 fps for
five seconds while the camera is off; counting frames in the last second reports 0.

## Run it

```bash
uv run python 02-rate-metrics/rate_metrics.py
```

## What you'll see

```
 t (s) what is happening           smoothed 1/gap  window count
   5.0 camera is OFF                       995 fps          0 fps
```

## The lessons

- A burst of frames 1 ms apart turns into "1000 fps" if you average 1/gap.
- A value that only updates on events freezes when events stop: a dead stream looks alive.
- For health metrics, **count events in a time window**. It can't spike above what really happened and it decays to zero on its own.

## For a post

**Screenshot:** `out/02-rate-metrics.png`: the shaded 'camera is off' band with one line flat at 0 and one stuck near 1000.

**Hook:** "My metrics said 1,000 fps. The camera was switched off."
1. Where the burst comes from (buffers flushing when a connection dies).
2. Why the EMA of 1/gap spikes and then freezes.
3. The one-line fix: count arrivals in the last second.
**Ask:** "What's your favourite metric that lied to you?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
