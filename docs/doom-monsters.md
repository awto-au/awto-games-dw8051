Current update: native monster movement and animation are implemented. Read [doom-actors.md](doom-actors.md). The static-sprite checkpoint below is retained for history.

# Static monsters in the native 8051 renderer

24 November 2026. The prototype now displays the original E1M1 monster
sprites. Six medium-skill, single-player map things are selected from THINGS:
four zombiemen and two imps. Original eight-angle A-frame patches, their
mirrored rotations, transparent holes, patch offsets and sector lighting are
used. This is a static-sprite checkpoint: monsters do not walk, attack, block
the player or take damage. Combat, pickups, sound, HUD and original thinkers
remain absent. Existing movement and manual doors still run natively.

The host converts WAD patches into column-major index/opacity pairs and packs
original thing coordinates. The simulated SDCC 8051 reads those records,
computes depth and view rotation, orders sprites back to front, obtains their
floor through the native BSP, projects them and writes the indexed pixels.
Per-column wall drawseg scales and top/bottom silhouettes clip the sprites.
The CPU also converts the completed framebuffer to RGB through MCU_DC DDR.
There is no host rendering or host-calculated sprite visibility.

## Run

The supplied current/ image can run with the patched repository and original
shareware doom1.wad, without rebuilding:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-monster-pose.json
```

Omit --pose for the normal map spawn. The monsters are farther into the level;
the supplied pose intentionally starts near two real map monsters. Keyboard
controls and /stream for VLC are unchanged. The IWAD and decoded asset RAM
are not included in the distribution.

Build using the awto-sdcc compiler and matching installed SDCC 4.5 linker and
large-stack-auto runtime, as documented in doom-doors.md. Two exact immutable
lookup tables (viewangletox and finetangent part 4) now reside in simulated DDR
to leave room in bank zero. tantoangle still uses its exact CODE high words.
The image uses 60,522 code/constant bytes and 1,869 dynamic XRAM bytes. The
existing fixed caches/mailboxes and runtime door states are retained. Observed
stack high-water D8h leaves 39 of 223 stack bytes. This build is a standalone
simulator image; monitor firmware integration and hardware flashing are absent.

## Protocol and limits

The existing boot/schema remains compatible. An additional two-word CODE
schema at F080h checks 12-byte thing and 16-byte patch records. DDR D0010h
holds a count and 16-byte header; D0020h holds up to 128 things (int16 x/y,
uint16 angle/kind, int32 native temporary depth). E0010h holds eight patch
records per kind (int16 width/height/left/top, uint32 pixels, uint8 flip,
three reserved bytes). Sprite pixels begin at DDR 400010h and use explicit
32-bit DdrRead addresses, outside the private generic-pointer heap. Each source
column is 128 (palette index, opacity) pairs. Source height is bounded at 128.
F6D0h exposes four uint16 counts: loaded, depth candidates, projected and
opaque pixel writes. Projected includes fully wall-hidden sprites.

Only supported monster types are selected; decorations, pickups and weapons
are not silently treated as monsters. Medium-skill flags and the multiplayer
exclusion flag are respected. Current rendering still approximates flat
floors/ceilings/sky, omits masked midtextures, and has no independent real-time
thinker scheduler. The clipper compares wall scale at each screen column to
the sprite plane, rather than integrating the original Doom actor pipeline.

## Captures and verification

current/doom-monsters-native.png is a nearest-neighbour enlargement of frame
10 of the actual 70-frame native walk. current/monster-walk-preview.mp4 plays
those CPU-written frames at 12 FPS for viewing. This playback speed is not a
hardware frame-rate measurement. The native model's worst frame in this walk
is 146.15 ms with 64 extra clocks per DDR command and the existing 350.791 MHz
CPU/flash/cache assumptions. Each completed pose, current door/collision
profile and palette conversion passes the independent checks. Stack wrap,
invalid DDR commands and busy-write hazards are zero.

The targeted run has 67 passing tests and one skipped test, assembled from
66 passing regressions plus the corrected independent fixture check. Logs are
in validation/. The fixture's expected geometry explicitly accounts for the
original half-step sine table (sin=25/cos=65535 at angle zero), map-floor
height, integer depth divisor, fixed-point sampling and transparent holes.
It asserts every output RGB pixel, opaque-write count and read-ready retry.
Other sprite checks cover real map filtering, full wall occlusion, rotation,
and independently booted versus multi-frame pixel equality. The original
310-frame door walkthrough, HTTP/MJPEG, movement/collision, cache/pointer and
DDR tests pass. No new 25 FPS claim is made.
