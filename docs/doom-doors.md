Current update: static monster sprites are implemented; see [doom-monsters.md](doom-monsters.md). The door checkpoint below is retained as historical documentation.

# Manual doors and keyboard walkthrough

Current milestone, 20 November 2026. Functionality takes priority over frame
rate; integration tests no longer require a minimum FPS. This is still a
standalone walkthrough prototype, not the original Doom game/thinker system.
Combat, monsters, pickups, keys, tagged triggers, sound and HUD are absent.

## What works

Native input can activate unlocked manual doors (linedef specials 1 and 31).
The CPU raises the sector ceiling by two map units per controller tick, up to
four units below the lowest neighboring ceiling. Special 1 waits 150 ticks,
then closes; special 31 stays open. A fresh use press can reverse a closing
door. Held use does not repeatedly activate it. Keys/other specials do not
silently open locked doors.

A closing door conservatively checks the player's 32-unit box against the
sector's bounding box. If the next height would intersect the 56-unit player,
it reopens without lowering the ceiling into the player. This conservative
box check can reopen near a concave sector; actors are not modeled yet.

Every height change writes the actual renderer sector and refreshes the top
of every linked collision portal from BOTH current neighboring ceilings.
The collision cache mapping is reacquired after sector reads, since those
reads can evict the profile. Native BSP/ceiling caches are invalidated too.
There are no host-computed door animations or collision decisions.

## Open-portal rendering correction

The previous renderer used a conditional assignment of the form
`backsector = condition ? &_g_sectors[index] : NULL`. With the current compiler
and our private DDR-pointer ABI, its generated code stored a zero third byte
instead of the loaded pointer tag. The renderer consequently read XRAM zeros
for the back sector and treated open portals as closed. This caused a black
view inside a thin doorway and made earlier rendering workloads misleadingly
small. Those earlier renderer/walking FPS claims are **not valid performance
results for the corrected renderer**. Arithmetic/DDR unit benchmarks are
separate and unaffected.

Preparation now emits an explicit null assignment followed by a conditional
pointer assignment. The generated code preserves the actual tag. Tests check
that views inside the open doorway have real scene pixels; the complete
animation verifies all collision profiles against the current native sector
heights and all player poses against an independent exact geometry oracle.
This is a source workaround for the private-ABI interaction, not a claim that
every standard SDCC pointer conditional is defective.

To fit the new gameplay code in bank zero, the unused angle32 function and
its helper are removed. The angle table keeps all 2049 exact high words used
by the renderer, saving space without changing angle16 results. Tests compare
all table entries against the original full-width values. Actor code needing
the removed angle32 entry point will need a corresponding implementation.

## Keyboard preview and VLC

Build with `scripts/doom_renderer.py`, supplying the original shareware IWAD:

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --out tmp/door-play --width 60 --height 128
python scripts/doom_play.py --out tmp/door-play --wad /path/to/doom1.wad \
  --pose examples/doom-door-pose.json
```

Open `http://127.0.0.1:8099/` on the machine running the simulator. W/S move,
A/D strafe, arrows turn, Shift increases speed, Space/E uses a door. The page
releases keys on lost focus, and stale movement input becomes neutral. Brief
use taps are latched until the next native frame. Stop ends the run cleanly.
For the ordinary map spawn omit `--pose`. The supplied pose starts in front of
a real E1M1 door; the demo is not a completed traversal from the map entrance.

VLC can open `http://127.0.0.1:8099/stream`; `/frame.jpg` supplies one native
capture. The server binds loopback only. Its host preview cap of 25 Hz does
not establish hardware throughput; the page displays the CPU-model frame
time. The controller still uses its fixed 35/25 tick schedule, not an
independent real-time catch-up scheduler.

The delivered executable directory includes CODE table values in tables.json.
An applied repository checkout, gcc/Python/numpy/Pillow and the user's IWAD
can run it without rebuilding with SDCC or supplying intermediate table .bin
files. The archive includes no original IWAD or preloaded asset RAM.

## Protocol and memory

Input at F610h is now six bytes: int8 forward/strafe, int16 turn, uint8 enabled,
uint8 buttons. Buttons bit zero is use. Existing omitted fields default to
zero. The boot record is 78 bytes, appending a door-data pointer after the two
collision pointers. The schema is 38 uint16 values and checks door definition
and state sizes (32 and 8 bytes). Collision records remain 16 bytes; the last
three bytes now identify front sector, back sector, and use token. Tokens
encode door ID + 1, with bit 7 selecting raise/stay. Same-height portals next
to dynamic doors remain in the collision index.

Door definitions are at DDR A0010h and linked linedef IDs at A2010h. E1M1 has
four supported door sectors / eight use edges. Runtime states occupy XRAM
F200h-F27Fh (16 x 8 bytes). Info at F6C0h-F6C7h records count, last used ID,
reopens, fault, activations and height updates. These are standalone protocol
addresses, not monitor registers, and need reconciliation with firmware
watchdog/feature storage before hardware integration.

Capture length now uses low byte F630h and high byte F632h, retaining ACK at
F631h. Runs can contain 1..65535 frames; the long sequence test exercises 310.
At 60x128 the corrected image occupies 59022 code/constant bytes and 1747
dynamic XRAM bytes. Fixed cache/scratch plus door-state allocation is 4400
bytes, plus mailboxes, within the documented 8 KiB XRAM. Observed stack peak
is D5h: 181/223 bytes used, 42 left. No hardware was flashed.

## Demonstration and checks

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --out tmp/door-demo --width 60 --height 128 --wad /path/to/doom1.wad \
  --pose examples/doom-door-pose.json --commands examples/doom-door.json \
  --latency 64
```

The 310 frames execute 434 native controller ticks: start against a closed
door, use it, enter the open doorway, obstruct its close, leave, turn around
and watch it close. There is one activation, one obstruction reopen and 80
height updates. Every completed frame passes native indexed/RGB consistency,
dynamic profile/sector-height consistency and independent collision checks.
The movie paced from model frame durations is about 37.96 seconds; a separate
12.4-second preview replays the same captures at 25 FPS. Neither is hardware
measurement. The corrected run's worst CPU-model frame is 205.16 ms; no speed
claim or minimum-rate gate is attached to this functional milestone.

119 targeted tests pass, alongside the opcode/stretch/timer/dual-DPTR checks.
Door fixtures cover range, front side, intervening solid walls, opening,
headroom/passability, waiting, closing, manual reversal, obstruction reopening,
raise/stay and use-edge handling. A forced cache-index collision verifies
profile-pointer reacquisition. End-to-end HTTP tests exercise input, quick-use
latching, invalid packets, JPEG/MJPEG output and clean stopping. A separate
live-stream check decoded 25 native MJPEG frames into H.264 with FFmpeg from
a build directory containing no intermediate table binary files.
