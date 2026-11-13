# Provider acquisition profiles

These are UI workflow guides, not fixed selectors or download APIs. Inspect the currently rendered interface and its language. Use the user's chosen provider; do not fetch hidden tiles, inspect credentials or silently replace it with another source. Offline stitching can use other providers' supplied screenshots without pretending their acquisition has been tested.

## Apple Maps

On macOS, use the Maps app or supported web UI according to the request and tool availability. On Windows, the intended path is a supported browser, not an assumed native Maps app. Confirm the requested satellite view and ruler are available in the actual interface. Hide/close place cards only after retaining location context. Prefer a flat view and fixed orientation. Native dragging can have inertia; measure short movements and adjacent-image geometry before scanning. A visible ruler can change in pixel length while retaining its terminal label.

The earlier macOS native-app run produced a full-area 98-frame interim mosaic. Cursor cleanup was unfinished when the session locked. That evidence does not validate Apple Maps web, Windows or a cursor-free end-to-end acquisition run.

## Google Maps — desktop browser

Open the supplied location link or locate the named WGS84 point in the current search UI, then verify nearby landmarks. Use the visible Layers / Satellite controls; do not reuse Apple Maps selectors or shortcuts. Use a flat top-down view, keeping browser zoom, orientation and viewport stable. Verify the live distance scale and units; do not apply mobile-app scale settings to the desktop site or assume every zoom can display exactly 50 m.

Close search/place panels after confirming the location when they obscure map pixels. Mask interface controls and record attribution appropriately. Keep labels/other overlays consistent with the request; do not replace Satellite with a different map type silently. Avoid mixing tilted/globe views into an otherwise flat scan.

Official desktop guidance: [layers and satellite imagery](https://support.google.com/maps/answer/3092439?co=GENIE.Platform%3DDesktop&hl=en), [web map versions](https://support.google.com/maps/answer/3031966?hl=en). Control locations can change; use observation rather than fixed screen corners.

## Yandex Maps — desktop browser

Open the supplied link or locate and verify the point using the current search UI. Choose the map-type control and the requested Satellite / Спутник or Hybrid / Гибрид mode. Hybrid includes cartographic labels; use it only when wanted and keep the choice consistent. Preserve a flat view and measure panning/zoom locally.

Do not confuse the distance-measurement tool (Линейка) with the displayed scale bar. Verify the actual scale label and units for the retained screenshots. If the required scale cannot be shown, seek a specific alternative rather than adding an artificial ruler.

Store task coordinates as separately named latitude and longitude. Yandex URL/API parameters may use longitude first: in particular `ll` is documented as longitude,latitude. Do not transfer the user's latitude,longitude pair blindly into a URL. Prefer the supplied link/current UI and confirm landmarks.

Official guidance: [map controls and map types](https://yandex.com/support/maps/en/concept/map-control), [coordinate order of ll and web map URL parameters](https://yandex.ru/maps-api/docs/static-api/request/map-center.html). The latter explains coordinates, not permission to switch this screenshot workflow to an API.

## Other supplied screenshots / other services

For existing images, proceed provider-independently using verified overlaps and consistent imagery/layers. For live capture from a service without a profile, perform a fresh UI/scale/cursor pilot and state the untested acquisition status. No new provider's UI, scale availability or image quality is guaranteed merely because offline rendering supports its image files.
