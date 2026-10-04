# Allow-lists beat block-lists for secrets in logs

Twelve URL shapes with a secret in them (user info, '@' in passwords, query strings, path
parameters, credentials in the path, fragments, stream keys, typos). The block-list leaks 7; the
allow-list leaks none.

## Run it

```bash
uv run python 06-url-redaction/redaction.py
```

## What you'll see

```
block-list leaked 7/12; allow-list leaked 0/12
```

## The lessons

- A block-list has to predict every place a secret can hide; real devices keep inventing new ones.
- An allow-list only states what a safe URL looks like: scheme, host, port, plain path. Everything else is `***`.
- If your rule names "bad" characters, it's a block-list. Over-redacting is the safe direction to be wrong in.
- Include the inputs you didn't plan for: typos and missing schemes are exactly the URLs that fail and get logged.

## For a post

**Screenshot:** The per-URL output: LEAK vs safe lines. All URLs are fake; the marker is literally `SECRET`.

**Hook:** "My password redactor kept losing. Here's why."
1. Three URL shapes that beat a simple regex.
2. Flip the rule: list what's allowed out.
3. The scoreboard: 7/12 leaks vs 0/12.
**Ask:** "What's the strangest place you've found a credential?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
