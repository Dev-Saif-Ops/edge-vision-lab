# The most secure allow-list is the shortest one

Seventeen URL shapes with a secret in them. Three redactors:

- **block-list**: hide what you know is secret (`user:pass@`, `?query`). Leaks **12/17**.
- **path-keeping allow-list**: keep scheme, host and a plain-looking path. Passes the first
  twelve URLs, then leaks **5/17**: the ones where the path itself is the secret.
- **shortest allow-list**: keep only the scheme and a host that really looks like a host.
  Leaks **0/17**.

The five URLs that beat the "smart" allow-list are real-world shapes: some NVRs give each
stream a random alias and the alias *is* the secret (`rtsp://nvr:7447/5nPr7RCmueGTKMP7`), some
cameras take the password as a plain path segment, a forgotten `@host` turns
`rtsp://admin:12345/...` into something that looks like host:port, and stream keys arrive
without a scheme.

## Run it

```bash
uv run python 06-url-redaction/redaction.py
```

## What you'll see

```
rtsp://192.168.1.1:7447/5nPr7RCmueGTKMP7
   (the stream alias IS the secret)
   block-list    LEAK  rtsp://192.168.1.1:7447/5nPr7RCmueGTKMP7
   path-keeping  LEAK  rtsp://192.168.1.1:7447/5nPr7RCmueGTKMP7
   shortest      safe  rtsp://192.168.1.1:7447/***

block-list    leaked 12/17
path-keeping  leaked  5/17
shortest      leaked  0/17
```

## The lessons

- A block-list has to predict every place a secret can hide; real devices keep inventing new ones.
- An allow-list is better, but only if it's **short**. Every "safe-looking" part you keep (a path,
  a bare word that looks like a host) is a place a secret can hide.
- Keep only what the log line needs. Here: which device failed, so scheme and host.
- Over-redacting is the safe direction to be wrong in.

## For a post

**Screenshot:** the UniFi-style block (three lines: LEAK, LEAK, safe) and the final scoreboard
(12/17, 5/17, 0/17). All URLs and secrets are made up.

**Hook:** "My password redactor passed every test. Then I met a camera whose URL path *was* the password."
1. Version 1, a block-list: leaked 12 of 17.
2. Version 2, an allow-list that kept "safe-looking" paths: looked perfect, leaked 5 of 17.
3. Version 3, keep only scheme and host: 0 of 17. The shortest rule won.
**Ask:** "What's the strangest place you've found a credential?"

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
