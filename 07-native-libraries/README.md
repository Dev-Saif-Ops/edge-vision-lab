# Know which native libraries your wheels bring

OpenCV and PyAV each ship their own FFmpeg. Install both and import them in one process, and macOS warns
that classes are "implemented in both ... may cause mysterious crashes".

## Run it

```bash
uv run python 07-native-libraries/native_libs.py
```

## What you'll see

```
av: 7 FFmpeg libraries
cv2: 7 FFmpeg libraries
2 separate copies of libavcodec: av, cv2.
objc: Class AVFFrameReceiver is implemented in both ... mysterious crashes.
```

## The lessons

- `pip install` can bring whole C libraries along, invisibly.
- Two copies of one library in one process is a time bomb for long-running services.
- Look inside your environment (`.dylibs`, `.libs`) before adding a second package that does the same job; pick one.

## For a post

**Screenshot:** The two-package listing and the objc warning (crop out your home-folder paths).

**Hook:** "A warning I almost ignored: 'may cause mysterious crashes'."
1. What a wheel bundles.
2. Two FFmpegs, one process.
3. The rule: one library per job, checked before adding a dependency.
**Ask:** "What's hiding in your site-packages?" 

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
