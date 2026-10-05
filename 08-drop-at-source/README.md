# Drop frames at the source, not at the end

A follow-up to [01](../01-newest-frame/). Keeping only the newest frame fixed memory, but a senior
engineer pointed out what it doesn't fix: every frame is still decoded before most are thrown
away. This experiment measures that.

## Run it

```bash
uv run python 08-drop-at-source/drop_at_source.py
```

## What you'll see

Numbers from a laptop. Yours will differ; the order and the ratios are the point.

```
way                           work per video second  model gets  per frame
decode all 60, keep 10                   15 ms (100%)     10 fps    2.76 MB
grab 60, convert 10                       6 ms ( 40%)     10 fps    2.76 MB
camera sends 10 fps                       3 ms ( 20%)     10 fps    2.76 MB
camera sends 10 fps, small                1 ms ( 10%)     10 fps    0.69 MB

One log line per frame: in memory 0.1 µs, written + flushed to disk 2.93 ms
```

The model gets the same 10 frames a second in every row. Asking the camera for 10 small frames
costs about a tenth of decoding 60 and dropping 50.

## In plain words

Think of a bakery. The oven makes 60 loaves a minute, the customer eats 10, and the other 50 are
thrown away. The customer always gets a fresh loaf, so from the outside everything looks fine.
But the flour, the gas and the work for 50 loaves were wasted. Better to tell the baker to make 10.

A camera doesn't send pictures. It sends **compressed** video, like a zip file, so it fits through
the network. Turning it back into a picture is called **decoding**, and it takes real CPU time.
Then the picture is converted to the colour format the code uses. Experiment 01's newest-frame slot
did both for all 60 frames, then dropped 50.

- **What 01 fixed:** memory. Only one frame is kept at a time.
- **What it didn't fix:** work. 50 frames a second are still decoded for nothing.

**Why can't the decoder just skip the frames we don't need?** Most video frames are not full
pictures. Every so often comes a full picture (a keyframe); the frames in between only describe
what changed since the one before. To decode frame 7 you need frame 6, and for frame 6 you need
frame 5. Skip one and the following frames break. So:

1. `grab()` instead of `read()` helps a little: every frame is still decoded, but only the frames
   you keep are converted to colour (row 2).
2. The real fix is upstream: ask the camera for 10 fps (row 3), and for a smaller picture if the
   model doesn't need a big one (row 4). Most IP cameras offer a low-resolution "substream" for
   exactly this, and camera modules let you set the frame rate and a second, smaller output.

## The second trap: disk writes

RAM is your pocket; a disk or SD card is a storeroom down the street. Writing one log line per
frame and making sure it reached the disk costs about **3 ms per frame here**. At 60 fps a frame
has 16.7 ms in total, so that is about a sixth of the budget gone, on a fast laptop SSD. An SD
card is much slower. On a device: keep logs in memory, send them over the network, and write to
disk only when something actually happened.

(On macOS a plain `fsync()` stops at the drive's own cache, so the script uses `F_FULLFSYNC` to
really reach the disk. With plain `fsync()` the number looks ~100x better than it is.)

## The lessons

- Dropping late saves memory but not work. **Drop as early as you can**, ideally before the data
  is even produced.
- A smaller frame helps twice: less to decode, less memory to move around.
- Per-frame disk writes, including log lines, are a hidden frame-rate killer on devices.
- Queues still have a place: a small buffer absorbs a short burst. They can't fix a steady
  mismatch between a fast producer and a slow consumer.

## For a post

**Screenshot:** `out/08-drop-at-source.png` and the terminal table.

**Angle (keep it humble):** a senior engineer's comment on my first post, and what I measured
after it.
1. My first experiment kept memory flat by keeping only the newest frame.
2. A senior pointed out that every frame was still decoded before being dropped. I measured it:
   asking the camera for 10 small frames was about a tenth of the work.
3. Bonus lesson from the same comment: one flushed log line per frame cost ~3 ms here, about a sixth
   of a 60 fps frame budget.

**Ask:** "What other early-drop tricks do you use on devices?"

*Everything here uses synthetic data and generic code: nothing about any employer's project.*
