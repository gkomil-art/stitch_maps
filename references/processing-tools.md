# Offline processing helper

Use a Python runtime containing NumPy, Pillow and OpenCV (SIFT support), installable from requirements.txt. Follow current dependency/permission rules. No machine-specific directories are embedded. On Windows use the selected Python interpreter (often `py` or `python`) instead of assuming `python3`. Commands below are otherwise identical on both systems.

## Existing screenshot batch

Create a UTF-8 manifest relative to its own directory:

```json
{
  "source": "Yandex Maps, user-supplied screenshots",
  "sources": [
    {"file": "captures/a.png", "row": 0, "column": 0},
    {"file": "captures/b.png", "row": 0, "column": 1}
  ]
}
```

Each source may include `crop` and `exclude` XYXY masks as in the scene schema below. List only permitted inputs, normally in capture order. Optional row/column indices add cross-row matching. For a small unordered set use `--all-pairs`; quadratic matching can be costly on a large collection.

```bash
python scripts/mosaic_tools.py align manifest.json --scene scene.json --report alignment.json
```

Default alignment uses validated integer translations with loop fitting. For authorized geometric correction add `--mode projective`. Projective initialization uses a maximum-support spanning tree and loop checks, not a global bundle optimizer. A disconnected graph or excessive loop error fails instead of writing a new scene. Supply missing overlap or improve the global model when needed; lowering the tolerance check is not a repair.

The scene initially encloses all valid source footprints and marks `extent_review_required`. Review it against the requested overview/boundary before rendering. Rotated/projective footprints can leave outer corner gaps in their rectangular envelope; choose the intended covered extent or take additional frames rather than padding with fabricated pixels. For a full rectangular grid of translations the initial extent is often already suitable. The PNG renderer still rejects all uncovered pixels.

The helper calculates initial transforms; the agent remains responsible for choosing the exact extent, detecting false repeated-pattern matches and inspecting seams. For large series that fail loop checks, use the joint native-correspondence optimization described in alignment-and-quality.md.

## Pair diagnostic

```bash
python scripts/mosaic_tools.py pair capture-a.png capture-b.png --crop-a 0 160 3340 2100 --crop-b 0 160 3340 2100 --report pair.json
```

All rectangles are XYXY in native pixels. Feature discovery can downscale analysis images; returned coordinates/transforms are native. The report maps **B to A**, reports robust geometric errors, spatial support, similarity scale/rotation and the 95th-percentile error left by integer translation. Inspect support and false-match risk; this is not automatic authorization to warp or a complete global alignment solver.

## Scene schema

After validating/optimizing the registration graph, write a scene with a common base plane:

```json
{
  "width": 512,
  "height": 256,
  "margin": 0,
  "source": "Apple Maps, newly captured satellite screenshots",
  "sources": [
    {"file": "captures/a.png", "crop": [0,0,332,256], "exclude": [[200,100,230,130]], "H": [[1,0,0],[0,1,0],[0,0,1]]},
    {"file": "captures/b.png", "crop": [0,0,332,256], "exclude": [], "H": [[1,0,180],[0,1,0],[0,0,1]]}
  ]
}
```

File paths are relative to the scene file; H maps full native source coordinates into the base plane. Crop and exclusion coordinates also refer to the full source. Margin defaults to 4 native pixels; plan coverage beyond boundaries so interpolation margins do not create holes. Set margin 0 only when valid for the processing mode, e.g. verified integer translations. Projective mode adds a 3-pixel buffer to exclusion rectangles for the cubic kernel; expand the specified box further if the actual cursor footprint is uncertain.

```bash
python scripts/mosaic_tools.py render scene.json --out map.png --report quality.json --ownership ownership.png --preview preview.jpg
```

Default strict mode rejects any transform beyond integer translation and copies pixels with nearest sampling. When geometric alignment is authorized:

```bash
python scripts/mosaic_tools.py render scene.json --mode projective --out map.png --report quality.json --ownership ownership.png --preview preview.jpg
```

Projective mode chooses a uniform output sampling factor from local Jacobians at nine positions per crop, retaining sampled native detail. Check more densely for strongly projective transforms. It uses one cubic resampling per source and chooses overlap ownership by distance to valid crop edges. It does not automatically correct tonal seams; inspect results and choose a better seam/blending method if needed.

The renderer checks free disk space, uses temporary disk-backed buffers, explicitly closes mappings before cleanup on success and failure, supports Unicode paths through image-byte decoding, rejects folded/singular transforms, counts uncovered pixels at full output resolution, and publishes PNG atomically only after coverage and integrity checks. quality.json records incomplete coverage on failure. It never synthesizes missing pixels. It is not a substitute for visual inspection, ruler verification, global alignment, or checking the source whitelist.

## Portable offline self-test

```bash
python scripts/test_mosaic_tools.py
```

Tests generate small synthetic images locally; they do not open a browser or download a map. They check pixel preservation, masks, initial batch alignment, disconnected-input rejection, geometric output sampling, Unicode paths, mapped-file closure and refusal to publish holes. Running this on macOS does not validate native Windows execution or live Google/Yandex capture. Run on the target Windows host before recording Windows as verified.
