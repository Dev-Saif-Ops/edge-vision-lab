# A test double can only confirm what you believe

Three threads open streams to a dead address. A fake capture finishes all three at 2 s; real OpenCV
finishes them at 2, 4 and 6 s: opens are serialised inside OpenCV.

## Run it

```bash
uv run python 04-test-doubles/serialised_opens.py
```

## What you'll see

```
  fake capture: finished at 2.0, 2.0, 2.0 s   (parallel)
  real OpenCV:  finished at 2.0, 4.0, 6.1 s   (serialised)
```

## The lessons

- A fake encodes your assumptions about the real component. If the assumption is wrong, the fake agrees with you anyway.
- For behaviour that depends on a library's internals (locking, timing, ordering), measure the real thing at least once.
- Keep one integration test against the real component that would fail if the behaviour changed.

## For a post

**Screenshot:** `out/04-test-doubles.png`: two rows of bars, side by side vs staircase.

**Hook:** "I wrote a test to prove my fix. The test was lying."
1. The symptom: one dead stream delayed every other stream's connection.
2. The fix that 'passed' its test, because the test used a fake.
3. Measuring real OpenCV: opens are serialised internally. Reads aren't.
**Ask:** "Has a mock ever told you exactly what you wanted to hear?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
