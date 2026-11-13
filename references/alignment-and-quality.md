# Alignment and quality

## Contracts

Strict pixel preservation permits integer translations, crop/mask operations and copying source pixels. Do not silently rotate, warp, blend or resample. Feature discovery may use reduced analysis images if coordinates are restored to native pixels.

Authorized geometric alignment permits warping while retaining output detail. This differs from preserving every input pixel unchanged. Never enlarge the overview to replace missing detailed captures.

## Registration graph

Detect features inside valid map pixels; SIFT with descriptor-ratio filtering and robust estimation worked in this case. Match sequential neighbours and adjacent rows, adding diagonal and loop constraints with real overlap. Use overview/reference anchors to control drift and orientation.

Sparse fields may fail overview matching yet match detailed neighbouring captures. Propagate validated native overlaps instead of rejecting such a frame solely for lacking an overview match. Check spatial support, error, orientation, local scale and plausible footprint. Repeated houses, crop rows and runway lines can produce false matches.

For a large series, jointly optimize native overlap correspondences with weaker global anchors. Check connectivity, median, high-percentile and worst local residuals; a low median can hide one bad seam.

The earlier Apple Maps 98-frame interim Qarshi mosaic covered its full rectangle and measured about 0.33 native-pixel median / 1.15 native-pixel 95th-percentile overlap error. These are case observations, not universal thresholds. Later cursor cleanup remained unfinished because the Mac locked; do not represent that stage as a completed validated result.

## Sampling and assembly

Express transforms in one reference plane. Sample Jacobians at corners, edge midpoints and centre; choose output sampling at least the maximum inverse smallest singular value among contributing sources. Use denser checks for strong projective distortion, reject folds/singularities, and resample each source once. A sufficiently large output dimension alone does not prove native detail was retained.

Keep validity and exclusion masks through warping. Retain interpolation margins. Use disk-backed arrays for large RGB, score and ownership buffers and check free space. Record source count, provenance, output dimensions, sampling and coverage diagnostics.

## Cursor replacement

Mask the actual cursor in each affected source. Prefer pixels from another overlapping source. If uniquely covered, take a cursor-free replacement; do not inpaint structural map detail or fill from the reference overview.

An interstitial capture can cover several cursor holes. Verify all projected holes fit its retained crop with margins; split the group if not. Camera corrections must use consistent coordinates: for source points q and retained interval [L,R], camera motion delta must satisfy delta in [max(q)-R, min(q)-L]. Do not subtract the viewport centre twice. Re-localize after moving.

## Acceptance

1. All contributing inputs belong to the permitted new-capture set; requested ruler labels were verified on those sources.
2. Validity masks exclude interface, pointers and unloaded imagery.
3. Registration is connected and passes global and local seam checks.
4. Every full-resolution output pixel has genuine source coverage after masks and interpolation margins.
5. Native-pixel inspection crosses actual ownership seams on meaningful landmarks; repair jumps, double edges and unacceptable tonal transitions.
6. The PNG decodes, its dimensions/size match the report, and delivery includes the full-resolution file. Previews are labelled separately.
