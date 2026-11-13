# Acquisition and recovery

Define a map crop from native screenshot dimensions, excluding toolbars, controls, repeated scale overlays and badges. Retain source attribution in the artifact/report as appropriate. Never bake display-specific coordinates into the skill.

## Pilot

Capture two or three overlapping frames before a long scan. Move the pointer to an observed blank title/toolbar region outside the retained map crop. Inspect the saved bytes at its former location; a white pointer/focus triangle can be part of the image rather than a display-only tool annotation.

Record both terminal ruler label and pixel length. Compare actual feature geometry too: a robust similarity/projective estimate reveals the error translation-only placement would leave. Do not attribute scale changes to terrain, projection or animation without evidence.

An OCR/template check must recognize the terminal distance **and unit**. Matching “50” inside a “75 m” ruler is insufficient. Calibrate templates to the current font/display, including a negative example. Do not reuse a template cropped from one user's map as a universal detector.

## Movement and settling

Drag inertia can greatly exceed the drag distance. Keyboard panning may be easier to measure, but duration-to-pixel conversions are not portable. Verify actual frame positions after each batch and re-calibrate after camera/viewport changes.

Use supported observations to establish stable geometry and loaded imagery. A fast burst of identical screenshots may be cached or too close in time to establish that an animation finished. Avoid blind retries and arbitrary long sleeps.

## Manifest

Use unique IDs and task-relative paths. Record file, timestamp, row/column, native dimensions, valid XYXY crop, exclusions and ruler verification. For example:

```json
{"id":"r02-c03","file":"captures/r02-c03.png","captured_at":"ISO timestamp","row":2,"column":3,"valid_crop":[0,160,3340,2100],"exclude":[],"ruler_label":"50 m","ruler_verified":true}
```

These rectangle values are illustrative, not defaults. Save screenshots, feature caches and registration JSON atomically: write a temporary file, close it, then rename it. A reader opening a partial NPZ/JSON file can appear to be an image-registration failure. Close file handles explicitly in long runs.

## Resume

Save location, reference/boundary, permitted geometric mode, capture whitelist, crop settings, latest validated viewport transform, completed coverage, unresolved defects, output paths and next semantic target. Store targets in reference/map coordinates rather than only queued keys.

After resuming, inspect the current application and screenshot first. Re-localize against saved imagery: the viewport may have moved, resized or changed scale. Check whether processing workers remain alive before starting duplicates. Do not trust stale UI indices, process state or precomputed movement commands.

A locked session requires manual unlock only for live acquisition; offline registration and verification can continue. Distinguish a usable interim PNG from a finished artifact.
