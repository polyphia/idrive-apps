## 0.6.25

- City/locality geocoding with nearby exact-name ranking and a 1500 km guard for automatic text destinations.
- Local road geometry fallback during missing routes and turn mismatches, with conservative junction matching.
- Production package excludes diagnostic capture UI, snapshots, USB exporters and diagnostic status rows.

## 0.6.20

- Reduce speed-limit sign to 75 px and center its number using visible glyph bounds.

## 0.6.19

- Replace camera warning banner with a 150 px speed-limit sign beside the nearest camera within 500 m, when its limit is known.

## 0.6.18

- Lighter, neutral white-gray roads and edges; cyan navigation and traffic colors retained.

## 0.6.17

- White camera-icon border with red camera lines; translucent red warning banner with white text.

## 0.6.16

- Add a Current street box On/Off setting for the name beneath the position arrow, independent of next-turn street text.

## 0.6.15

- Independently show, hide, move and resize the turn street text. Adjustable box width and height; long names wrap upward and overflow ends with an ellipsis.

# Changelog

## Unreleased

- Add independent map width/height percentages anchored at the car arrow.

- Resolve internet names using uplink lease DNS; support bounded gzip responses and exact Portuguese postal-code matching.

- Remove manual destination-capture controls; destination reading remains automatic.

- Remove diagnostic recording and USB exporters; read destination text through memory-only IPC.

- Import the current local HUD app, destination capture and navigation fixes.
- Use release-time version stamping and resolve the app dependency with `next`.
