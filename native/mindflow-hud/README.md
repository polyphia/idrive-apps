# HUD map service

Road tiles, phone maneuver guidance, destination capture, inferred route geometry and HUD rendering.
See [the app documentation](../../apps/robertn_hud_map/README.md) for behavior and limitations.

`component.json` lists the complete installed payload, including the destination reader and its Alpine runtime.
Runtime origins and checksums are in `adapter-runtime/SOURCES.json`; vendored dependencies retain their licenses.
Private routing credentials and captured car data are not part of this source package.

## Validation

Run from the repository root:

```sh
node native/mindflow-hud/test/navigation_display_test.js
node native/mindflow-hud/test/navigation_state_test.js
node native/mindflow-hud/test/navigation_progress_test.js
node release/release.js check mindflow-hud robertn_hud_map
```

The release check builds committed HEAD twice. The app uses `package/` and requires `mindflow-hud: next`;
release stamping resolves that dependency to the actual native release version. Both new components start at 0.6.13.

Outbound DNS uses `/run/mgu-uplink/lease.json`. Route responses allow at most 16 MiB decoded JSON and 8 MiB compressed data. Portuguese postal-code queries must match the returned country and postcode; postcode coordinates represent an area, not a doorstep.
