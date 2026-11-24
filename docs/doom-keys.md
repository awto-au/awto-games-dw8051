# Native key inventory and coloured manual doors

Historical format-7 checkpoint. Read [doom-switches.md](doom-switches.md) for
the current format-8 image, tagged switches and validation.

24 November 2026. The 8051 now collects keys, keeps their inventory bits,
rejects a manual door without the required colour and opens it after a matching
card or skull has been collected. The key is retained. HUD squares show owned
colours and flash for a rejected use; the browser names owned/missing colours.
All gameplay, use tracing, door movement and pixels remain native instructions.
This continues the standalone prototype, not the original Doom thinker system.

## Play the reproducible test scene

E1M1 has no original keys or coloured locks. The supplied demonstration explicitly
changes the use specials on an existing door and adds a blue card before boot.
It preserves the original map geometry and uses the original shareware artwork.
This is an initial test scene, not an unmodified E1M1 playthrough. No host scene
edits run after the CPU starts. Only player input is supplied during play.

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad \
  --pose examples/doom-keys-pose.json --scene examples/doom-keys-scene.json
```

Press Space/E at the closed door to see the blue-key request. Back up to collect
the card, move forward again, then release and press use to open the door.
W/S moves, A/D strafes, arrows turn, Shift increases speed and F/Ctrl fires.
Existing input is edge-triggered: holding a rejected use does not automatically
open the door when the key is acquired. Health/ammo and combat remain enabled.

Replay the recorded 86-frame locked-door encounter with:

```sh
python scripts/doom_renderer.py --skip-build --sdcc /path/to/awto-sdcc/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto --out /path/to/current \
  --wad /path/to/doom1.wad --latency 64 \
  --pose examples/doom-keys-pose.json --scene examples/doom-keys-scene.json \
  --commands examples/doom-keys-demo.json
```

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together. The BIN is the complete 128 KiB two-bank image.
See doom-renderer.md for rebuilding with the awto-sdcc fork and SDCC 4.5 runtime.
The IWAD, decoded assets and proprietary SDK are not included.

## Keys and lock mappings

| Colour | Card thing / sprite | Skull thing / sprite | Inventory mask accepted by lock |
| --- | --- | --- | --- |
| Blue | 5 / BKEY | 40 / BSKU | 1 or 8 |
| Yellow | 6 / YKEY | 39 / YSKU | 2 or 16 |
| Red | 13 / RKEY | 38 / RSKU | 4 or 32 |

Cards and skulls have separate persistent bits. Collecting a duplicate of the
same key leaves that item on the floor. Either form of a colour opens its lock;
other colours do not. Opening never consumes inventory. Key collection uses
the existing native contact, height and live wall checks. Keys do not change
health/ammo and cannot be collected after death. Restarting creates a new session.

| Manual linedef special | Required colour | Existing standalone door action |
| --- | --- | --- |
| 1 | None | Raise, wait, close |
| 31 | None | Raise and stay |
| 26 / 32 | Blue | Wait-close / stay |
| 27 / 34 | Yellow | Wait-close / stay |
| 28 / 33 | Red | Wait-close / stay |

Requirements belong to each use line, so two sides using the same sector can
have different locks. Range, front-side selection, wall occlusion, use edges,
ceiling updates and conservative obstruction reopening remain in effect.
A missing key sets a colour notice for 35 controller ticks and increments the
rejection count. The notice clears on expiry or successful use. The original
Doom source establishes the colour/card/skull and special-number mappings:
[p_doors.c](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/p_doors.c)
and [info.c](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/info.c).
Door timing/control remains the earlier standalone approximation.

The supplied shareware IWAD contains card sprites but no skull-key sprites.
All three card colours render from original assets. Skull inventory/unlock
logic is tested with explicit initial fixtures using card pictures; original
skull artwork is not claimed tested. The loader accepts skull sprite kinds
when the supplied IWAD contains them and reports missing artwork otherwise.
There is no generated substitute artwork. Bonus/key sprites use their A frame.

The renderer remains bounded to maps of at most 512 linedefs and 128 monsters,
16 manual-door sectors and 128 total pickups. Original E1M2/E1M3 exceed the
linedef bound; adding locks does not make those complete maps supported yet.
Tagged switches/triggers and other door specials remain future work.

## Protocol, memory and checks

D805 format 7 enables keys and coloured manual-door packing. Older images retain
their earlier pickup/special handling. Existing boot, input, combat, actor,
door-definition/state, pickup-counter and projectile record sizes are unchanged.
Pickup rules 5-10 identify blue/yellow/red cards then blue/yellow/red skulls.

A profile's use byte encodes door ID (bits 0-4, IDs 1-16), required colour
(bits 5-6: 0 none, 1 blue, 2 yellow, 3 red) and stay-open (bit 7). Native use
tracing returns that byte; DoorTick checks inventory before changing any state.
XRAM F748h has four uint16 values: owned mask, required-colour notice (1/2/4),
rejection count and notice ticks. F740h pickup counters retain their layout.

Bank-zero code/constants use 63,429 bytes. Bank-one gameplay C uses 5,741 bytes
plus 15 entry bytes, ending at 667Dh in its audited overlay. Dynamic XRAM is
2,119 bytes (2,040 bank zero plus 79 gameplay bank), plus fixed caches/mailboxes.
The image remains two 64 KiB banks. Existing simulator bank wiring is still
unverified on monitor hardware. No hardware was flashed; source remains uncommitted/unpushed.

The final suite has 163 passing tests with no skips: the preceding 121 plus
42 key/lock cases. Tests cover matching/mismatched cards and skulls, all six
special numbers, per-line locks sharing a sector, both door actions, retained
inventory, duplicate keys, native HUD pixels, wall occlusion, rejection edges,
notice expiry, old images and collection while use remains held. The complete
native combat, pickups, fireballs, maths, bank, geometry, DDR and HTTP suite
remains passing. See validation/keys-final-tests.log.

The patch now also includes scripts/mcs51_ddr.h, previously present in the
source bundle but accidentally omitted from the patch. A clean checkout of the
exact base was patched, the complete native image rebuilt byte-for-byte, a
fresh simulator compiled and native lock rejection verified. No pre-existing
compiled simulator is needed to restore this checkpoint.

## Capture

The silent model-paced video contains two separately initialized test scenes:
25 frames showing a visible blue card and collection, then 86 frames showing
lock denial, card collection, successful use and passage through the door.
The main encounter ends with one rejection, one successful activation and the
blue-card bit still owned. All 111 frames are real CPU-written captures.

Native state, accounting, geometry, bank return, RGB conversion and DDR checks
pass for every frame. No stack wraps, invalid DDR commands or busy-write hazards
occurred. Worst model frame is 273.92 ms. Stack high-water is DBh, leaving 36
of 223 stack bytes. Timing still assumes 350.791 MHz and 64 extra clocks per DDR
command; playback is not measured hardware FPS. The fixed 35/25 controller-tick
budget remains unchanged. Functionality still takes priority over FPS work.
