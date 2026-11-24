# Native player movement and collision milestone

**Superseded renderer timing:** [the door/walkthrough milestone](doom-doors.md)
fixes a lost back-sector DDR pointer tag. Earlier renderer/walking FPS figures
below under-rendered open portals and must not be used for the corrected
renderer. Functionality now takes priority; no minimum FPS is enforced.
Arithmetic and DDR unit checks remain applicable.

Implemented 20 November 2026, continuing the standalone [Doom renderer](doom-renderer.md).
The CPU now accepts per-frame movement commands, runs bounded controller ticks,
checks nearby static walls/portals, slides along walls, steps up and follows
floors. Python loads assets, writes input and checks completed output; it does
not choose the player position, collisions, camera or rendered pixels.

This controller is original bring-up code, **not Doom's original player thinker
or physics**. There are no actors, combat, door activation, pickups, momentum,
friction, gravity, jumping, bobbing or sound. It snaps down to a supporting
floor. Input currently comes from a JSON script or native mailbox, not a live
keyboard window. Those limitations are part of this milestone.

## Native work and asset preparation

`fw/doom/motion.c` executes as SDCC MCS51 opcodes. Forward/strafe commands are
clamped to +/-8 map units per tick; turn is clamped to +/-4096 angle16 units
(22.5 degrees). Native sine/cosine and optimized FixedMul project movement.
A full-vector attempt falls back to separate axes for sliding; a failed pure
axis attempt is not redundantly retried. Bounded displacement cannot jump
across an entire 32-unit player box in one tick.

The controller advances 35 ticks for every 25 rendered frames with the pattern
1,1,2,1,2 ticks. This is a fixed schedule for a 25 FPS simulation, **not a
hardware timer or real-time catch-up scheduler**. If rendering misses that
rate, this harness does not independently maintain 35 wall-clock ticks/sec.

Collision uses a 32x32 box and a 56-unit player height; upward steps are limited
to 24 units. Fixed-point boxes round outward to map units for conservative
integer segment tests. Cross-product bounds are validated by the asset packer:
coordinates within +/-16000, map spans <=16384 on each axis, <=512 lines.
The controller queries BLOCKMAP cells and uses a visited bitmap to avoid
checking duplicate line IDs. Lines are copied from DDR through DdrMapRead and
the native 16-byte copy routine before geometric tests.

The offline loader prepares one aligned 16-byte profile per original linedef:
endpoints, highest adjacent floor, lowest adjacent ceiling and flags. Solid or
explicitly player-blocking lines remain solid. Portals with changed floor or
ceiling are marked separately. Static same-height portals cannot block this
controller and are removed from the prepared BLOCKMAP lists; original IDs
are retained and duplicate cell lists are shared. E1M1's map shrinks from
6922 to 4644 bytes. This is collision asset preparation, not host physics.
Dynamic sectors will need updated profiles and indexing before doors/lifts
can be implemented.

A native BSP callback updates the centre sector when a height-changing portal
touches the player box. Otherwise the cached centre heights remain valid.
The supporting floor is the highest floor under the whole box, and headroom
the lowest ceiling. A centre-only floor snap initially got stuck on downward
steps; the unit fixtures cover that regression. Combined portal headroom is
checked before committing a move. Invalid headers/lists and failed cache maps
report a fault; list traversal is bounded.

## Input and telemetry

All addresses below are this standalone executable's protocol, not scaler
registers. They must be reconciled with firmware/watchdog storage before
hardware integration. The additional telemetry overlaps addresses used by
other firmware features; none of those features run in this harness.

| XRAM input at F610h | Type | Meaning |
|---|---|---|
| +0 | int8 | forward, negative is backward |
| +1 | int8 | strafe, positive is left |
| +2 | int16 LE | turn per tick in angle16 units, positive counterclockwise |
| +4 | uint8 | enabled; zero retains the renderer-only camera mode |

| XRAM state at F6A0h | Type | Meaning |
|---|---|---|
| +0, +4 | int32 LE | x, y in signed 16.16 |
| +8 | uint32 LE | angle, full turn = 2^32 |
| +12, +14 | int16 LE | supporting floor and limiting ceiling |
| +16 | uint32 LE | completed controller ticks |
| +20 | uint8 | blocked axes this frame: bit 0 X, bit 1 Y |
| +21 | uint8 | ticks executed this frame |
| +22 | uint8 | fault: 1 map/count, 2 list, 3 DDR map, 4 initial headroom |
| +23 | uint8 | controller enabled for this frame |

Collision records are at DDR 00080010h, the prepared BLOCKMAP at 00090010h.
The boot record expands from 66 to 74 bytes, appending those two addresses.
The linked schema now has 36 uint16 values and checks record/input/state sizes
16/5/24. WAD yaw conversion now uses exactly 2^32 units per turn.

## Walking workload and 25 FPS

The 180-command [input script](../examples/doom-walk.json) walks into a wall,
then strafes/turns and walks through further viewpoints. The native controller
executes 252 ticks. Seventy-six frames report a blocked axis. Every completed
pose passes an independent exact-rational segment/box test against **all**
475 profiles, independent of the native BLOCKMAP query. This oracle only
checks output; it never adjusts native positions.

Same CPU/flash/DDR assumptions as the renderer: 350.791 MHz, 3:1 CPU/flash,
modeled shared flash cache including MOVC data misses, 32 MiB DDR, 64 additional
CPU clocks per DDR command, SDK-default MOVX stretch, direct-bus MPAGE assumed.

| Walking viewport | Frames | Worst frame | Slowest equivalent FPS |
|---|---:|---:|---:|
| 30x48 | 180 | 39.9597 ms | 25.0252 |
| 30x64 | 180 | 41.8011 ms | 23.9228 |
| 40x64 | 180 | 51.0579 ms | 19.5856 |

The 30x48 run has only about 0.0403 ms of spare budget. Its maximum controller
phase is 2.5803 ms (including camera update); frame timing includes movement,
logical clearing, rendering, RGB conversion, DDR writes and final flush.
The larger moving workload is slower than the earlier stationary-position
rotation: it includes controller work **and different, heavier viewpoints**.
The controller-linked image also shifts flash layout: the former 40x80
renderer-only preset now misses 25 FPS (24.78 in the eight-angle integration
check). It remains covered for pixel correctness; 40x64 is the guarded
renderer-only preset. Previous 40x80 timing records are historical.

At 30x48 the image uses 1349 dynamic XRAM bytes plus 4272 fixed cache/scratch
bytes and mailboxes, within the documented 8 KiB MCU XRAM. Occupied code and
constants total 58974 bytes. The observed stack reaches D5h: 181 of 223 bytes
used, 42 remaining. There are no invalid DDR commands, busy-write hazards or
PUSH wraps in the walking sweep. These are tested paths, not proof that future
actor code or every map fits. No hardware has been flashed or timed.

## Reproduce and verify

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --wad /path/to/original/doom1.wad --width 30 --height 48 \
  --yaw 0 --commands examples/doom-walk.json --latency 64 \
  --out tmp/doom-walking/30x48
```

Each JSON list item is one frame's command, for example
`{"forward":4,"strafe":0,"turn":0,"enabled":1}`. Omitted movement fields are
zero and enabled defaults to one. `--commands` determines the frame count;
the current capture protocol permits 1..255 frames per run. Disabled input
retains the old renderer-only rotation option.

`renderer-results.json` contains each pose, tick count, blocked axes, collision
oracle result, controller clocks and full-frame clocks. `frame-NNN.png` is the
CPU-written BGR888 raster. The H.264 walking movie plays 180 such captures at
25 FPS; its encoded cadence is for viewing, not the performance measurement.

109 targeted tests pass, plus opcode/stretch/timer/dual-DPTR checks. Native
fixtures cover blocked walls, passable portals, 24/25-unit steps, 55/56-unit
headroom, downward steps, sliding, diagonal walls, no tunnelling at clamped
maximum input, signed commands, cardinal rotation, turn limits and the tick
schedule. A real-WAD input test checks every pose and compares three captured
moving frames byte-for-byte with independent cold renders at those native
poses. Existing math, DDR, cache, MOVC and renderer tests remain enabled.
