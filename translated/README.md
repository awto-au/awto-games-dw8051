# Complete supplied-WAD translation

Source SHA-256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`

Preserved 1264 of 1264 original lumps; decoded 968 patches, 54 flats and 125 composite textures. All 14 palettes and all COLORMAP bytes are retained.

DPAK is a ZIP-compatible indexed asset bundle. Every payload has a SHA-256 entry in manifest.json. Indexed pixels and coverage masks retain transparent posts, patch origins, frame rotations and mirroring. Raw sound/music/interface data and all map lumps remain byte-exact. Normalized levels retain every original field, special, tag and thing flag. The original Doom8088 state graph, frame brightness, frame durations, symbolic actions and thing definitions are translated as metadata. BSP, sidedef, linedef, subsector, blockmap and REJECT references are validated.

| Map | Lines | Sectors | Segs | Native pack | Native capture |
|---|---:|---:|---:|---|---|
| E1M1 | 475 | 85 | 732 | passed | passed |
| E1M2 | 1033 | 200 | 1463 | passed | passed |
| E1M3 | 1026 | 177 | 1445 | passed | passed |
| E1M4 | 830 | 139 | 1172 | passed | passed |
| E1M5 | 825 | 143 | 1141 | passed | passed |
| E1M6 | 1352 | 250 | 1862 | passed | passed |
| E1M7 | 958 | 170 | 1371 | passed | passed |
| E1M8 | 333 | 74 | 586 | passed | passed |
| E1M9 | 653 | 147 | 978 | passed | passed |

## Runtime boundary

Standalone native controller/combat and renderer. Original Doom thinkers, complete weapon/inventory rules, sector effects, lifts, teleports, intermission and campaign progression remain unported.

Translated assets are complete for this supplied WAD. The supplied shareware WAD contains E1M1 through E1M9, not the registered episodes or Doom II. Unsupported native line/sector specials and thing types are listed per level in translation-report.json, with original data retained in the bundle. Conversion does not turn an unported action into a working game mechanic.

## Reproduce

`python3 scripts/doom_translate.py --wad /path/to/doom1.wad --native /path/to/built-firmware --verify-native --out /path/to/output`
