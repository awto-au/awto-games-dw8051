# Native ranged attacks and fireballs

Historical format-5 checkpoint. Read [doom-pickups.md](doom-pickups.md) for the
latest format-6 image, native health/ammo items, validation and captures.

24 November 2026. Soldiers now fire deterministic ranged shots, and imps throw
visible fireballs. Balls travel independently of the shooter, can be dodged,
impact walls or the player and show the original explosion frames. All attack,
trajectory, collision, damage and rendering decisions execute as native 8051
instructions. This remains a standalone prototype, not vanilla Doom thinkers.

## Run and controls

Apply doom-ddr.patch to the exact repository base, then run the supplied image:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-fireballs-pose.json
```

The supplied pose faces a real E1M1 imp. Omit --pose for the usual map spawn.
W/S moves, A/D strafes, arrows turn, F/Ctrl fires, Space/E uses doors and Shift
increases movement speed. Strafing dodges an already launched fireball. Health,
ammo, pistol/death behaviour and session restarting remain as in doom-combat.md.
The original shareware IWAD is required and is not included.

**Keep doom_renderer.bin, doom_renderer.ihx and banking.json together.** The BIN
is the complete two-bank image. The IHX alone contains only bank zero and is
insufficient for this checkpoint. The runner checks the combined image hash and
its bank-zero bytes before executing it. tables.json and cache-config.json are
also required, as in earlier supplied builds. No rebuild is needed to run the
supplied current/ with the patched repository and Python/gcc dependencies.

## Native rules and rendering

Attack windup now activates out to a 512-unit box. At impact the CPU rechecks
live sight. Within the existing close-range box it applies 10 contact damage.
At greater range soldiers apply 10 immediate damage if their shot height
intersects the player's body; imps allocate a fireball. Both keep the earlier
eight-tick windup, recovery and locomotion timing. Pistol damage and ammunition
rules are unchanged. Walls can block an already prepared soldier attack.

Eight fireball slots are bounded in DDR. Launch records the shooter position
and current player direction once. Velocity uses signed 8.8 fixed point with
an eight-unit maximum axis component per controller tick; diagonal Euclidean
speed can consequently be greater than eight. There is no homing. Position is
16.16 fixed point, and each tick has four substeps of at most two units per
axis. The CPU traces each substep against live wall/portal profiles at the
constant launch height, shooter floor + 32. Thus a closed door or a too-low
opening blocks it. The projectile is a point for world collision and uses a
20-unit player hit box with a body-height test. It does 10 damage.

Original BAL1 A/B patches animate flight; C/D/E animate impact for four ticks
each. Balls expire after 105 moving ticks or resolve on a wall/player impact.
A full pool drops the new shot without overwriting an existing slot. A ball
continues after its shooter dies. Source/target counters, trajectories and
animation state are CPU-owned. They do not collide with other monsters, and
there is no infighting, vertical aiming/gravity or splash damage yet.

Sprites share the native back-to-front wall-clipped render pass with monsters,
using the stored projectile height and full brightness. The host only packs
original assets, supplies input and checks/captures completed CPU-written
frames. It does not move projectiles, select impacts or draw their pixels.

## Two code banks and memory

The original code bank was full. Unused full-sine entry points were removed,
and the approximate quarter-wave wrappers were compacted without changing
any of the 8192 original sine/cosine samples. That alone did not leave enough
room, so projectile routines now execute in a second native code bank.

Bank zero contains 62,861 code/constant bytes. The projectile engine contains
3805 bytes of C code plus a nine-byte entry table, at addresses 5000h onward
in bank one. The complete executable is 128 KiB, two 64 KiB banks. Bank one
copies the common prefix and the callable bank-zero routines, overlaying only
the audited 5000h-5EECh window. Native assembly wrappers select the bank, call
the engine and restore bank zero before returning. There are no host function
stubs or native-opcode replacements. Instruction/flash timing uses the existing
5000h common-prefix cache model.

The build audits direct external code references against the overlay, reserves
engine XRAM after BOTH ordinary and initialized bank-zero data, rejects local
DATA/bit storage and initializer areas, and bounds code/XRAM growth. The engine
adds 46 XRAM bytes after the 2034 bytes used by bank zero, totaling 2080 dynamic
bytes, plus the earlier fixed caches/mailboxes. Observed capture stack high
water is D8h, leaving 39 of the 223 stack bytes. Every captured frame verifies
that execution returned to bank zero; the demonstration has 360 bank switches.

Bank selection uses the existing simulator's MOVX FFFFh model. Its wiring to
actual monitor firmware/registers and hardware scanout remains unverified.
No monitor was flashed, and source remains uncommitted and unpushed.

## Data layout

The D805 marker version is now 5; legacy version 4 soldier-mask headers are
still packed for the retained older image. Version 5 uses a separate attack-kind
table because header word one now counts render records. Schema addresses from the combat checkpoint
are retained. DDR D0010h holds three uint16 words: monster count, render count
(monsters + 8 slots), and fireball patch-kind ID, followed by padding to 16
bytes. Original 20-byte monster records are followed by eight render records.
For a fireball the existing floor field holds its absolute sprite height,
awake is phase (1 flight, 2 impact), and health is the active flag.

DDR D3010h holds attack-kind words (imp or soldier). D6010h holds eight 16-byte
physics records: int32 fixed x/y, int16 8.8 vx/vy, uint16 age and owner. The
FF94h CODE schema records physics size and slot count. XRAM F720h has eight
uint16 counters: spawned, successful substeps, wall impacts, player hits,
reserved, expirations, dropped allocations and slots visited in the last tick.
The last counter is not a post-update occupancy count. Counters wrap modulo
65536. Fireball metadata is appended as one additional 12-frame patch kind;
the original WAD and decoded asset RAM are not bundled.

## Demonstration and validation

The 127-frame capture faces the original imp, dodges its first fireball, turns
back toward it, takes a hit from the second and kills it with three pistol hits.
Final health is 90, ammo 42, shots 8, hits 3 and kills 1. Two balls are launched;
one hits a wall and one hits the player, with 231 successful native substeps.

current/doom-fireballs-model-paced.mp4 is approximately paced from full CPU-model
frame durations, 25.05 seconds. current/doom-fireballs-preview.mp4 replays the
same CPU-written frames at 12 FPS for convenient viewing. Worst model frame is
349.44 ms at the existing assumed 350.791 MHz CPU and 64-extra-clock DDR command
latency. This includes native game/physics, bank switching, rendering, HUD,
RGB conversion and flush; it is not measured hardware FPS. There is no minimum
FPS gate. The controller still advances fixed 35/25 ticks per rendered frame.

104 tests pass with no skips. The current regression logs cover exact native evaluation of all 8192 sine and
cosine samples, two-bank execution/return, a fireball hitting after its owner
dies, dodging, wall impact, simultaneous pool exhaustion, soldier shots and
wall-blocked windups. Runtime checks verify fixed-point/render-position
agreement, speed bounds, constant trajectories, allocation/resolution accounting,
ammo, health/damage, kills, player/actor geometry and RGB conversion. The older
combat, 310-frame door, movement, HTTP/MJPEG, cache/private-pointer, DDR and
arithmetic regressions are retained. See validation/ranged-regressions.log
for the final count and status.

Next gameplay gaps include pickups, keys/tagged triggers, more weapons,
sound, restart flow and a real-time tick scheduler. Floors/ceilings/sky still
use flat approximations. Ranged rules remain deterministic approximations;
monster-to-monster impacts, vertical aiming and vanilla Doom AI are absent.
