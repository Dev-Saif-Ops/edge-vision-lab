"""A tiny mutation tester: plant one bug at a time, run a test file, see if it notices.

Coverage tells you which lines ran. Mutation testing tells you whether your tests would
notice if those lines were wrong.

Run:  uv run python 05-mutation-testing/mutate.py
"""

import ast
import io
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "backoff.py").read_text()

MUTANTS = [
    ("no cap", "min(initial * 2**attempt, cap)", "initial * 2**attempt"),
    ("linear instead of exponential", "initial * 2**attempt", "initial * (attempt + 1)"),
    ("no jitter", "uniform(ceiling / 2, ceiling)", "uniform(ceiling, ceiling)"),
    ("full jitter instead of equal", "uniform(ceiling / 2, ceiling)", "uniform(0, ceiling)"),
    ("off-by-one attempt", "2**attempt", "2**(attempt + 1)"),
    ("negative check removed", "if attempt < 0:", "if False:"),
]


def string_spans(source: str) -> list[tuple[int, int]]:
    """Character ranges of strings and comments, which a mutation must never touch."""
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    spans = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.STRING, tokenize.COMMENT):
            (r1, c1), (r2, c2) = tok.start, tok.end
            spans.append((offsets[r1 - 1] + c1, offsets[r2 - 1] + c2))
    return spans


def mutate(source: str, old: str, new: str) -> str:
    """Replace the first occurrence of `old` that is in CODE, not in a docstring or comment.

    The first version used source.replace(old, new, 1). The pattern also appeared in the
    docstring, so it "mutated" the documentation, the code never changed, and the strong tests
    were reported as missing bugs that had never been planted. Always check that a mutant
    really changed the code.
    """
    spans = string_spans(source)
    start = 0
    while (i := source.find(old, start)) != -1:
        if not any(a <= i < b for a, b in spans):
            mutated = source[:i] + new + source[i + len(old) :]
            ast.parse(mutated)  # a mutant must still be valid Python
            return mutated
        start = i + 1
    raise ValueError(f"pattern not found in code: {old!r}")


def survives(test_file: str, source: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "backoff.py").write_text(source)
        shutil.copy(HERE / test_file, tmp)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_file],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


if __name__ == "__main__":
    for tests in ("test_weak.py", "test_strong.py"):
        assert survives(tests, SOURCE), f"the unmutated code must pass {tests}"
    print(f"{'planted bug':<32} {'weak tests':>12} {'strong tests':>14}")
    print("-" * 60)
    score = {"test_weak.py": 0, "test_strong.py": 0}
    for name, old, new in MUTANTS:
        mutated = mutate(SOURCE, old, new)
        assert mutated != SOURCE
        cells = []
        for tests in score:
            lived = survives(tests, mutated)
            score[tests] += not lived
            cells.append("SURVIVED" if lived else "caught")
        print(f"{name:<32} {cells[0]:>12} {cells[1]:>14}")
    n = len(MUTANTS)
    print(
        f"\nweak tests caught {score['test_weak.py']}/{n}; strong tests caught {score['test_strong.py']}/{n}."
    )
    print("Both test files run every line of backoff.py. Only one of them would catch a bug.")
