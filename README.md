# Edge Vision Lab

Small, standalone experiments from my journey into embedded vision and edge systems.

I build products end to end, on my own: design, code, deployment, operations and SEO
([RailTC](https://railtc.in), [Aya ToolWall](https://toolwall.aya-ai.xyz) and others). Now I'm
going down the stack, to cameras, video streams and devices at the edge. Each folder here is one
lesson I learned the hard way, turned into a script you can run in a few seconds.

| # | Experiment | The lesson in one line |
|---|---|---|
| 01 | [Newest frame](01-newest-frame/) | Queue every frame and you get 3.5 GB of memory and a 5-minute wait after one minute |
| 02 | [Rate metrics](02-rate-metrics/) | Averaging 1/gap reports ~1000 fps while the camera is off; count a window instead |
| 03 | [Backoff and jitter](03-backoff-jitter/) | Without jitter, 200 devices hit a recovering server in the same instant |
| 04 | [Test doubles](04-test-doubles/) | A fake said parallel; real OpenCV opens streams one at a time |
| 05 | [Mutation testing](05-mutation-testing/) | Two test files, both 100% coverage: one caught 0/6 bugs, the other 6/6 |
| 06 | [URL redaction](06-url-redaction/) | Block-list leaked 12/17, a "smart" allow-list 5/17, the shortest allow-list 0/17 |
| 07 | [Native libraries](07-native-libraries/) | Two packages, two copies of FFmpeg, one "mysterious crashes" warning |
| 08 | [Drop at the source](08-drop-at-source/) | Decoding 60 frames to keep 10 is ~10x the work of asking the camera for 10 small ones |

## Run

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if you don't have uv
uv sync
uv run python 01-newest-frame/newest_frame.py     # any experiment; charts land in out/
uv run pytest                                     # checks every experiment still shows what it claims
```

Python 3.12, NumPy, OpenCV, Matplotlib. No camera, GPU or account needed: everything uses
synthetic data.

## Rules for this repo

- Generic engineering only, synthetic data only. Nothing from any employer's project: no
  product names, use cases, architecture, customers or code.
- Every number in a README comes from running the script, and a test keeps it honest.

## Licence

[MIT](LICENSE)
