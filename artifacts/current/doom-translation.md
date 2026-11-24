# Whole-WAD graphics and level translation

Updated 25 November 2026. Format 10 consolidates all supplied Episode 1 assets
and levels in one conversion command, rather than adding one map per checkpoint.
The input used for validation is the 4,196,020-byte shareware Doom IWAD, SHA-256
`1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`.

## Convert and verify everything

Build the native firmware with scripts/doom_renderer.py as documented in
[doom-renderer.md](doom-renderer.md), then run:

```sh
python3 scripts/doom_translate.py --wad /path/to/doom1.wad \
  --native /path/to/built-firmware --verify-native --frames 24 \
  --out /path/to/translated
```

The command translates every map and asset before producing the per-map native
DDR packs and executing the optional native captures. Errors stop conversion;
unsupported gameplay actions remain explicitly listed in the audit. The output
contains 1,264 original lumps, 968 decoded patches, 54 flats, 125 composed wall
textures, all 14 palettes, all colour maps and all nine original E1M1-E1M9 maps.
Every original lump is retained, including sound, music and miscellaneous data.
The original Doom8088 info.c graph is also translated: 314 states and 49 thing
definitions, including frame numbers, fullbright flags, durations and symbolic
action names. This state metadata does not execute an unported thinker.

`doom-assets.dpak` is a ZIP-compatible archive with manifest.json, SHA-256 per
payload, raw lumps in original order, decoded graphics and normalized map JSON.
The .idx graphics contain row-major palette indices; .mask files contain 0/255
coverage, so opaque palette index zero remains distinct from transparency.
Patch offsets, frame rotations, dual-name mirrored rotations, composed texture
patch positions, dimensions and source indices are retained. Names in normalized
map records preserve their original case. Raw map records round-trip byte-exact.

Normalized maps retain THINGS, LINEDEFS, SIDEDEFS, VERTEXES, SEGS, SSECTORS,
NODES and SECTORS fields; BLOCKMAP cells/lists and REJECT matrices remain intact.
All special numbers, tags, difficulty and multiplayer flags are retained. The
converter validates geometry references, BSP graph/leaf references, subsector
ranges, blockmap termination and REJECT size, plus texture/flat references.

## Native runtime changes

- Collision capacity is 2,048 original linedefs, covering the supplied nine maps.
  The 256-byte visited bitmap occupies fixed MCU XRAM F100-F1FF, after the frame
  bitmap and before door states. It no longer consumes dynamic XRAM.
- Door capacity is 32. States occupy F200-F2FF. A 256-entry uint16 action table at
  DDR A6010 lets a collision profile retain its byte-sized use token while
  distinguishing 32 doors, coloured locks, repeat buttons, stay-open and exits.
  Descriptor bits 0-5 hold the 1-based id, 6-7 the key colour, 8 stay-open,
  9 switch, 10 repeat. Token zero remains no action. Header offset 12 points to
  this table. Switch records remain 16 bytes, with a uint32 target mask.
- Demon/Spectre and Baron original art/rotations now load, with health 150/1000.
  Demon/Spectre attacks are melee-only. The existing small animation/combat
  state machine remains a prototype; the Baron currently uses the imp fireball
  behaviour/art. Complete original sprite frames and state data are in DPAK.
- Native plane sampling replaces solid-colour floors and ceilings. Original
  64x64 flat indices are sampled in world coordinates with fixed-point native
  arithmetic and original COLORMAP data. Original SKY1 pixels replace the solid
  sky; native view-angle table entries determine cylindrical sky columns.
- Bank 2 contains the native HUD and plane/sky routines. All executable banks
  retain their common dependencies, imports are checked against overlay ranges,
  dynamic XRAM is allocated consecutively, and the wrapper restores bank 0.
  Keep the complete 196,608-byte three-bank BIN and its matching IHX, banking.json,
  tables.json and cache-config.json together. IHX alone is insufficient.
- Graphics parameters occupy fixed MCU XRAM F300-F323. The flat pointer directory
  is at DDR 140010; SKY1 columns at 160010; flat pixels start at 800010.

Each `native/E1Mx/ddr.zip` holds a sparse 32 MiB scene image: 4 KiB nonzero blocks,
block hashes, the exact boot mailbox and firmware/source hashes. Everything is
validated before the loader writes memory. The CPU receives all data before
boot. Host input after boot consists of controls; projection, BSP traversal,
visibility, clipping, texture sampling, sprites, combat and RGB output execute
as SDCC-generated 8051 instructions through the DDR simulator.

## Play any translated map

The original WAD is not needed when using a converted native folder:

```sh
python3 scripts/doom_play.py --out /path/to/translated/native/E1M6 \
  --packed /path/to/translated/native/E1M6
```

Alternatively use `--wad /path/to/doom1.wad --map E1M6` against the firmware
folder. Open the printed local preview. W/S moves, A/D strafes, arrows turn,
F/Ctrl fires, Space/E uses, Shift increases movement speed. The native capture
can also run headlessly with doom_renderer.py --skip-build --packed plus the
normal compiler/linker/libdir arguments required by that CLI.

## Translation completeness and runtime boundary

The supplied WAD's graphics and level data are translated and retained in full.
It does not contain the registered episodes or Doom II assets. All nine maps
can load independently; this is not yet a complete Doom campaign. Original
sector thinkers, damaging floors, lifts, stairs, crushers, walk triggers,
teleports, full weapon/armor/powerup rules, decorative thing behaviour,
intermission/next-level routing and sound playback remain unported. Masked
middle-texture rendering and full vanilla lighting/animation are also unfinished.
Their original data is preserved, not silently discarded or treated as working.
Per-map unsupported line/sector specials and thing types are listed in the
machine-readable report. Unsupported pickups/decorations are not yet drawn by
the native actor pass; their complete art is available in the translated bundle.

Functional tests include native pixel-by-pixel plane/sky arithmetic, original
patch transparency/zero-index checks, full archive hashing, lossless map-record
round trips, line 2047 collision, door 32 and target bit 31, odd-health overkill,
translated-image checksum failure, and all preceding gameplay regressions.
Native captures check stack wrap, DDR hazards/invalid accesses, bank restoration,
RGB palette output, geometry, movement and native resource/state accounting.
CPU-model timing is recorded, not measured hardware performance. Hardware bank
selection, memory wiring and scanout remain unverified. No hardware was flashed.
