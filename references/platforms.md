# macOS, Windows and validation status

## Common interface contract

Use current supported computer/browser tools; the skill itself provides neither a browser extension nor an OS-control bridge. Respect a user-selected app/browser. Inspect tools and available windows before using a saved target. Offline processing needs only image files, writable disk space and a suitable Python environment.

Record actual saved pixel dimensions, per-frame crops, browser zoom and display scaling. Tool coordinates may be window-local, region-local or otherwise specified by its current documentation. Do not divide/multiply coordinates by Retina/DPI factors by guesswork.

## macOS

Apple Maps can use its native app when available; browser profiles use an available supported browser. Use the documented command-key naming and window selection of the current tool. Move the pointer to a safe blank toolbar area before captures, and verify saved map pixels are clean. Do not apply fixed crop coordinates or movement durations from the earlier Qarshi session.

## Windows

Use an available supported desktop browser for Google/Yandex Maps and, if appropriate and accessible, Apple Maps web. Identify the exact browser/app window through the tool inventory; do not invent a native Apple Maps application. Refresh observation and screenshot-region mapping before coordinate actions when required by the tool. Use Windows-specific input conventions from current tool documentation, not blind Command-to-Control substitutions.

DPI settings such as 125%/150%, multiple monitors and browser zoom can alter screenshot pixels, controls and rulers. Keep settings fixed during the scan and calibrate crops from saved images. Do not change system display/security preferences merely to make the workflow easier.

For local Python use pathlib and UTF-8 JSON, retain original filenames (including spaces/Cyrillic), and close file-backed arrays/images before temporary-file cleanup or atomic replacement. Do not install macOS binary wheels on Windows. Install dependencies for the selected interpreter/platform; if no Python/tool bridge exists, clearly state that prerequisite instead of claiming support is active.

## Honest validation matrix

| Component | Evidence |
|---|---|
| Apple Maps native on macOS | Real prior acquisition and full-area interim mosaic; cursor cleanup remained unfinished |
| Provider-independent image helper on macOS | Synthetic pixel-preservation, masks, geometry and failure checks; re-run after changes |
| Google Maps / Yandex Maps browser profiles | Written against official documentation; no live end-to-end acquisition validation in this session |
| Native Windows acquisition / Python execution | Intended portable workflow; no Windows host test performed |

The new changes can test Unicode paths, mapped-file closing and failure behavior on macOS, which improves portability but does not constitute a native Windows test. Before stating a combination is verified, run a small real capture/stitch pilot on that OS/provider, record the tool/browser versions and inspect output. Missing live control blocks capture, not stitching of supplied files.
