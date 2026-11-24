# Native health and ammunition pickups

Historical format-6 checkpoint. Read [doom-keys.md](doom-keys.md) for the latest
image, key inventory, coloured manual locks and current validation.

24 November 2026. The 8051 now loads, renders and collects original E1M1 health
and ammunition items. Soldier shots, imp fireballs, pistol combat, collision,
manual doors and HUD remain enabled. This is a standalone gameplay prototype;
the original Doom thinker system is not running. Functionality precedes FPS work.

## Play and reproduce

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together in current/. Then run:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad \
  --pose examples/doom-pickups-pose.json
```

Walk over items to collect them. W/S moves, A/D strafes, arrows turn, Shift
moves faster, F/Ctrl fires and Space/E uses a manual door. At death, stop and
rerun the simulator. Omitting --pose starts at the original map spawn.

The main supplied capture faces an original medikit, takes damage from a real
imp and walks over the medikit. Replay it with:

```sh
python scripts/doom_renderer.py --skip-build --sdcc /path/to/awto-sdcc/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto --out /path/to/current \
  --wad /path/to/doom1.wad --latency 64 \
  --pose examples/doom-pickups-pose.json \
  --commands examples/doom-pickups-demo.json
```

To rebuild, omit --skip-build and add the SDCC 4.5 --linker path described in
doom-renderer.md. The banked BIN is required, as in the fireball checkpoint.
The original shareware IWAD and decoded asset RAM are not bundled.

## Rules

| Original thing | Sprite | Native effect | Capacity |
| --- | --- | --- | --- |
| 2011 stim pack | STIMA0 | Up to 10 health | 100 health |
| 2012 medikit | MEDIA0 | Up to 25 health | 100 health |
| 2014 health bonus | BON1A0 | 1 health | 200 health |
| 2007 ammunition clip | CLIPA0 | Up to 10 bullets | 200 bullets |
| 2048 ammunition box | AMMOA0 | Up to 50 bullets | 200 bullets |

An item remains if its resource is already at or above that item's capacity.
Partial gains clamp to capacity and still consume the item. A bonus can raise
health above 100; ordinary medicine will not reduce that health or be consumed.
Items disappear exactly once and do not respawn. They never block movement,
actors, projectiles or doors. Bonus sprites currently show their first frame.

Collection requires a 20-unit box on each map axis. The item's native floor
must lie from eight units below the player's feet through 56 units above them.
The CPU also checks live wall/portal sight at item floor + 4, so nearby items
behind a wall cannot be collected. These are simplified deterministic rules.

Pickups run before weapon, projectile and monster updates in each existing
controller tick. Full-health medicine remains available if a later attack
causes damage. A dead player cannot collect or be revived. A five-tick palette
border acknowledges collection; damage/death borders take precedence. The
browser also reports the native collection count alongside health and ammo.

## Native implementation and layout

The asset converter filters original map things for medium skill and excludes
multiplayer-only placements, consistent with existing monster loading. E1M1
contains 19 supported pickups across all five types. At most 128 are accepted;
both the packer and native initialization enforce the bound.

CODE marker D805 version 6 enables pickup loading. Versions 3-5 retain their
previous asset layouts and behaviour. DDR D8010h holds the uint16 pickup count
in a 16-byte header. After the monster records and eight fireball render slots,
the same 20-byte render records hold pickups. Their tics field is the rule
index (0 stim, 1 medikit, 2 bonus, 3 clip, 4 box); health is the active flag.
Native initialization finds each item's floor from the BSP. Ground items use
their sector lighting; fireballs retain their separate full-bright rendering.

XRAM F740h holds four uint16 values: collected count, effective health added,
effective bullets added and flash timer. FF98h advertises the 128-item bound
and eight-byte counter layout. Existing actor/combat/boot/input record sizes
and fireball physics addresses remain unchanged. Native sprite capacity is
264 records: 128 monsters, eight fireballs and 128 pickups.

Collection executes in bank one beside fireballs, using two extra native
trampolines at 5009h and 500Ch. Bank-zero callers switch and restore banks;
the host does not substitute gameplay or rendering. Bank-zero code/constants
use 62,950 bytes. Bank-one gameplay C uses 5,630 bytes plus 15 entry bytes,
ending at 660Eh inside the audited overlay. Dynamic XRAM totals 2,113 bytes:
2,034 bank-zero bytes and 79 gameplay-bank bytes, plus fixed caches/mailboxes.
The complete image remains 128 KiB in two native banks.

## Verification and footage

The final suite passes 121 tests with no skips. Seventeen pickup tests cover
all item rules, effective healing, both capacity limits, retained excess items,
repeat contact, movement through unneeded medicine, walls, vertical separation,
death, skill/multiplayer filtering, old-image compatibility and item-count
limits. An independent WAD post decoder and fixed-point projection compare
every original clip pixel against the CPU-written frame. Existing native
combat, projectiles, exact sine/cosine, bank return, movement, doors, DDR,
private pointers, HTTP/MJPEG and HUD tests remain passing.

Every captured frame checks item identity, irreversible consumption, collection
range/height, resource accounting, player/actor geometry, native bank return,
RGB conversion and DDR errors. The host only loads initial assets/input and
checks/captures results. It does not collect items, change resources, aim,
move actors or draw game pixels for the 8051.

The 27.23-second video has three separately initialized original E1M1 scenes:

| Scene | Native frames | Result |
| --- | --- | --- |
| Health bonus | 71 | Health 100 to 101 |
| Ammunition clip | 73 | Bullets 50 to 60 |
| Medikit under attack | 135 | Two imp attacks reduce health to 80; medikit restores 100; a later hit leaves 90 |

All 279 frames are CPU-written captures, approximately paced by recorded model
durations. Playback includes MP4 timing quantization. Worst frame across these
three views is 174.77 ms. These are scene-dependent model durations, not
measured hardware FPS or a speed improvement claim. The model still assumes
350.791 MHz CPU and 64 extra clocks per DDR command. Controller ticks still
follow the existing fixed 35/25-per-frame budget.

Capture stack high-water is D7h, leaving 40 of 223 stack bytes. No stack wraps,
invalid DDR commands or busy-write hazards occurred. Hardware register wiring,
memory contention, scanout and integration remain unverified. No monitor was
flashed; changes remain uncommitted/unpushed.

Next work includes keys/tagged triggers, weapons/armor inventory, sound,
restart flow and a real-time tick scheduler. Floors/ceilings/sky still use
the preceding approximations. The longer video from the previous checkpoint
remains a separate deliverable; it predates pickups.
