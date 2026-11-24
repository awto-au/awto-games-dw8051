# Native soldier ranged attacks

24 November 2026. Soldiers now use deterministic hitscan attacks in the
standalone 8051 combat prototype. Imps retain their close-range attack.
Functionality remains the priority; this is not vanilla Doom's combat system.

## Run and reproduce

Use the supplied current/ firmware, original shareware IWAD and current source:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-ranged-pose.json
```

F/Ctrl fires, W/S moves, A/D strafes, arrows turn, Shift moves faster and
Space/E uses a manual door. At death, stop and rerun the simulator.

Build and record the supplied fight with the existing compiler/runtime setup:

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --out tmp/doom-ranged --wad /path/to/doom1.wad --latency 64 \
  --pose examples/doom-ranged-pose.json \
  --commands examples/doom-ranged-demo.json --frames 130
```

## Native behaviour

Every 32 locomotion ticks, an awake soldier can enter an eight-tick attack
windup when the player is within 512 units on each map axis and the sight ray
is clear. At impact the CPU checks the current range, live portal/wall heights
and whether the ray at the player's eye height intersects the shooter's body.
A hit removes 10 health. Recovery lasts 27 ticks; the soldier must then reach
another locomotion check. Imps use a 48-unit box with the same windup/recovery.
Pain or death cancels a pending attack. Attack attempts are counted even if
the impact check rejects them. There is no spread, randomness, tracer,
projectile, actor interception or saved aim point. The simplified attack tracks
the player's current position until impact; moving behind a wall can block it.

The packer identifies soldiers from map thing types 3004 and 9. A uint16 mask
at DDR D0012h marks their map-local kind indices. It supports a map containing
only soldiers and maps where kind ordering differs. Older firmware gets a
zero mask. CODE marker D805 version 4 advertises the new behaviour. Actor and
combat record layouts, boot record and input protocol are unchanged.

Host code only prepares assets/input and captures/verifies results. Attack
decisions, timing, visibility, damage, animations and every framebuffer pixel
execute as compiled 8051 instructions through simulated DDR.

## Validation and capture

98 unique tests passed across the existing regression suite, combat tests and
the separately enabled arithmetic check. The regression run initially skipped
that arithmetic check because its assembler-path variable was absent; it was
then explicitly enabled and passed. Logs are retained in validation/.
New coverage checks ranged soldier damage, melee-only imps, windup/recovery,
blocked/out-of-range impact rejection, pain/death interruption, map-local kind
masks and old-image compatibility. Existing native pistol, HUD, actor, door,
movement, DDR, pointer, HTTP/MJPEG and arithmetic checks remain passing.

The 130-frame original E1M1 capture ends with two soldier kills, 70 player
health and 41 rounds remaining after nine shots. Three successful monster
attacks remove 30 health. Every captured state passes native accounting and
geometry checks. No stack wrap, invalid DDR command or busy-write hazard was
observed. The two soldiers fire before the player starts shooting.

current/doom-ranged-model-paced.mp4 approximately follows the recorded CPU
model durations, totalling 20.98 seconds. current/doom-ranged-preview.mp4
replays the same frames at 12 FPS for convenient viewing. These playback rates
are not hardware measurements. Worst assumed CPU-model frame: 248.08 ms.
The unchanged model assumes 350.791 MHz CPU and 64 extra clocks per DDR command.

The 60x128 firmware uses 63,752 code/constant bytes and 2,029 dynamic XRAM bytes,
in addition to fixed caches/mailboxes. Stack high-water is DBh, leaving 36 of
223 stack bytes. Monitor memory mapping, contention and scanout are unverified.
No hardware was flashed; changes have not been committed or pushed.

Next gameplay work includes imp projectiles, pickups, keys/tagged triggers,
more weapons, sound, restart flow and a real-time tick scheduler. Flat plane
and sky approximations remain. Read doom-combat.md for the preceding pistol,
HUD and actor record details; its contact-only behaviour and old capture
figures describe that historical checkpoint.
