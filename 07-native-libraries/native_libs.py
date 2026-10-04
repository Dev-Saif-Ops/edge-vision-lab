"""Which native libraries did your Python packages bring with them?

Many Python wheels bundle compiled C libraries. Two packages can each bring their own copy of
the same library (FFmpeg is the classic case: OpenCV and PyAV both ship it). Loaded into one
process, two copies can clash; on macOS the runtime warns "Class X is implemented in both ...
This may cause spurious casting failures and mysterious crashes."

Run:  uv run python 07-native-libraries/native_libs.py
      uv run --with av python 07-native-libraries/native_libs.py   (add PyAV to see two copies)
"""

import re
import site
import sys
from collections import defaultdict
from pathlib import Path

LIBRARY = re.compile(r"^lib(av(codec|format|util|device|filter)|sw(scale|resample))[.\-]")


def bundled_ffmpeg() -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    # Every site-packages on the import path: `uv run --with` adds packages in an overlay
    # environment that site.getsitepackages() doesn't list.
    roots = {Path(p) for p in sys.path if p.endswith("site-packages")} | {
        Path(p) for p in site.getsitepackages()
    }
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and LIBRARY.match(path.name):
                package = path.relative_to(root).parts[0]
                found[package].append(path.name)
    return dict(found)


if __name__ == "__main__":
    found = bundled_ffmpeg()
    if not found:
        print("No bundled FFmpeg libraries found.")
    for package, libs in sorted(found.items()):
        print(f"{package}: {len(libs)} FFmpeg libraries")
        for name in sorted(libs):
            print(f"    {name}")
    codecs = [p for p, libs in found.items() if any(n.startswith("libavcodec") for n in libs)]
    print()
    if len(codecs) > 1:
        print(f"{len(codecs)} separate copies of libavcodec: {', '.join(codecs)}.")
        print("Import both packages in one process and they can clash. Pick one.")
    else:
        print("One copy of FFmpeg. Try: uv run --with av python 07-native-libraries/native_libs.py")
