# Coverage says what ran; mutation testing says what would be caught

Two test files both execute every line of a small backoff function. Plant six bugs: the weak tests
catch none, the strong tests catch all six.

## Run it

```bash
uv run python 05-mutation-testing/mutate.py
```

## What you'll see

```
planted bug                        weak tests   strong tests
no cap                               SURVIVED         caught
off-by-one attempt                   SURVIVED         caught
...
weak tests caught 0/6; strong tests caught 6/6.
```

## The lessons

- 100% line coverage with assertions like `> 0` proves almost nothing.
- Write each test by asking "which bug would get past this?"
- **Check the checker.** The first version of `mutate.py` replaced the first text match, which was inside the docstring. It "planted" bugs in the comment and reported the strong tests as weak. It now skips strings and comments and refuses a mutant that changes nothing.

## For a post

**Screenshot:** The terminal table (0/6 vs 6/6). For a second post: the docstring bug in `mutate.py`.

**Hook:** "Both test files had 100% coverage. One caught 0 bugs, the other caught 6."
1. What mutation testing is, in one sentence.
2. The two test files side by side.
3. Twist: my mutation tool itself had a bug, and how I caught it.
**Ask:** "Do you measure test quality beyond coverage?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
