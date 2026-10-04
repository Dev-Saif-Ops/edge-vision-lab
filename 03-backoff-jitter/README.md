# Backoff needs jitter, and jitter has a price

200 devices lose their server together and retry. Without jitter they all hit the recovering server in
the same instant; with jitter the worst moment is ~10–18x smaller, but the last device reconnects later.

## Run it

```bash
uv run python 03-backoff-jitter/backoff_jitter.py
```

## What you'll see

```
strategy        retries  peak / 0.5 s  peak once server is back  all back after
fixed 1 s          4000           200                       200          20.0 s
exponential        1000           200                       200          31.0 s
full jitter        1207           144                        11          48.6 s
equal jitter       1031           200                        19          48.2 s
```

## The lessons

- Exponential backoff alone cuts total retries, but keeps everyone in **lock-step**.
- Jitter breaks the lock-step. **Full** jitter (`uniform(0, d)`) spreads most; **equal** jitter (`uniform(d/2, d)`) keeps a minimum wait.
- The real decision is a trade-off: smaller spikes vs slower full recovery. Equal jitter's first retry still clusters (the window is narrow at the start).

## For a post

**Screenshot:** `out/03-backoff-jitter.png` (log scale; the exponential line shows the synchronized spikes) and the table.

**Hook:** "Exponential backoff is half the story."
1. The thundering herd: everyone retries at 1, 3, 7, 15, 31 s together.
2. Full vs equal jitter, with the numbers.
3. The price: recovery takes longer. Pick based on what your server can absorb.
**Ask:** "Full or equal jitter in your systems, and why?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
