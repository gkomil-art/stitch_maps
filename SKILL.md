---
name: stitch-maps
description: Stitch overlapping map screenshots into a full-resolution PNG, or capture a bounded area from Apple Maps, Google Maps or Yandex Maps before stitching. Use for satellite/map screenshot mosaics, including сшивка скриншотов карт, on macOS or Windows. Does not generate imagery, provide directions, or automatically download map tiles.
---

# Stitch Maps

Build a real-image map mosaic from permitted screenshots. Separate provider/OS acquisition from provider-independent image processing. Never switch the requested map provider or combine different providers' imagery silently.

## Choose the mode

**Existing screenshots:** preserve originals; inspect their overlap, dimensions, orientation, layer, scale and interface. Coordinates and an overview are useful for extent/orientation but are not mandatory when the requested extent is already unambiguous. Do not browse, open Maps or ask for computer control merely to stitch local files. If rulers are absent, do not claim a verified metric scale.

**New capture:** first resolve provider, URL, exact WGS84 latitude/longitude and overview/boundary. Read [providers.md](references/providers.md) for the chosen provider and [platforms.md](references/platforms.md) for the current OS. A full rectangular overview is the default boundary only when no outline is drawn; state that assumption. Default to satellite imagery and a visible 50 m ruler if unspecified; preserve any explicitly chosen layer or scale. If the exact label is unavailable, agree on an alternative rather than fabricating or silently changing it.

For a missing boundary or ambiguous location, clarify only the missing information. Keep latitude and longitude separately named; URL parameter order is provider-specific.

## Processing contract

- **Strict pixels:** integer translations, cropping/masks and original pixel copying. No rotation, scaling, perspective warp or blending. If native overlap diagnostics show this cannot meet seam requirements, show the evidence and request a mode change.
- **Geometric alignment with native detail:** when permitted by the task, fit scale/rotation/perspective and choose output sampling that does not reduce the finest source detail. Resample each source once. This is different from preserving every input pixel unchanged.
- Preserve exclusions such as “new captures only”; keep an explicit input whitelist. An overview anchors extent/orientation and does not supply output pixels unless explicitly requested.
- Use a single provider/layer/imagery set per mosaic by default. Different dates, roof parallax, 3D views and moving objects may not admit exact alignment; report unresolved seams rather than inventing detail.

## Acquisition pilot

Read [capture-and-resume.md](references/capture-and-resume.md) when taking new images or resuming acquisition.

1. Inspect current tools and UI, select a flat view and stable orientation/viewport, and register an overview to the requested boundary.
2. Capture adjacent pilot frames before a full scan. Check the terminal ruler label **including units**, actual feature geometry, useful overlap and loaded tiles. The same “50 m” text can have different pixel lengths.
3. Move the pointer outside the retained map crop using an observed safe UI location. Inspect saved pixels at the old pointer position. Verify panning still works after focus changes. Do not repeat a full scan with a burned-in pointer.
4. Save full native captures atomically; record per-frame valid crop, exclusions, physical pixel dimensions, display/browser zoom, provider and scale evidence.
5. Scan with measured overlap (usually 25–35% in both axes), adapting to feature scarcity. Update coverage from actual registered positions; do not equate key duration, zoom level or planned frame count with geometric coverage.

Never reuse macOS coordinates, shortcuts, crop masks or ruler templates on Windows without a fresh pilot. Follow the current computer-use tool contract, including its OS-specific window and screenshot coordinate handling.

## Alignment and output

Read [alignment-and-quality.md](references/alignment-and-quality.md). Use native overlap correspondences and loop constraints, with weaker global anchors if available. Check connectivity, spatial support, plausible footprints and local errors; repeating roofs/roads can yield false matches.

[scripts/mosaic_tools.py](scripts/mosaic_tools.py) offers pair diagnostics, initial batch alignment with connectivity/loop checks, and masked rendering. It does not acquire imagery or perform full global projective bundle optimization. See [processing-tools.md](references/processing-tools.md). Review the proposed extent and refine transforms when loop/seam checks fail; do not force a rejected alignment into rendering.

Keep crop, cursor and interpolation masks through registration, coverage and compositing. A unique obscured or missing area requires a real replacement capture (or a clear incomplete result if capture is unavailable), not inpainting or low-resolution overview pixels. Close gaps at the requested boundary and inspect full-resolution coverage, not only a preview.

Inspect native-pixel crops crossing actual ownership boundaries through markings, roofs, road edges and fields. Repair unacceptable jumps, double edges, tonal seams, UI remnants and pointers. Verify PNG decoding and report dimensions, size, provider, source count and any remaining defects. Link the full-resolution PNG; label previews separately.

## Capability and interruption

Acquisition requires an available supported computer/browser-control tool and an accessible session; the skill does not install or grant those capabilities. If unavailable, continue with user-provided screenshots or explain the concrete blocker. Do not require a live browser or internet for offline stitching.

Save resumable semantic targets and validated transforms. On a locked Mac or Windows session request manual unlock; do not bypass authentication/UAC/CAPTCHA or change security/power settings. Offline processing may continue. Re-localize after resume rather than executing stale movements.

Distinguish documented workflows from tested combinations: see [platforms.md](references/platforms.md). Do not advertise untested Windows or Google/Yandex end-to-end runs as verified. Do not mark the task complete with unresolved coverage/cursor/seam work. Follow current UI-tool completion-summary requirements once the observed UI part finishes.
