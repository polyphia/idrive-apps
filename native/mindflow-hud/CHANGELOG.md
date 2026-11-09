# Changelog

## Unreleased

- Map width and height adjustable independently (25-200%).
- Map no longer blanks when Android Auto recalculates the route.
- Faster cyan line correction after a missed turn; Vela is re-queried only after the phone's new turn settles.
- Route line kept (clipped if disputed) during short gaps in phone guidance.
- More reliable local road line, including dense city centres.
- Better handling of GPS noise and 5-10 Hz positioning; fewer false reroutes.
- Map re-centring no longer drops HUD layers.
- Missed-turn simulation test.
- Uplink lease DNS, gzip responses and Portuguese postal-code matching.
- Destination reading is automatic; diagnostic recording and USB exporters removed.
- Release-time version stamping.

## 0.6.26

- Centre places the selected turn panel or street box at the canvas centre. Safer inward defaults and bounds keep movement/resizing within a 40 px canvas inset. Existing saved positions are constrained on load.

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
