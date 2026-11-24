Current update: pistol/contact combat and health are implemented. Read [doom-combat.md](doom-combat.md). The movement-only checkpoint below is retained for history.

# Native ground-monster movement and animation

24 November 2026. The E1M1 prototype now wakes nearby monsters through native
sight checks, animates their original A-D walking frames, and moves them toward
the player. Player and monster bodies block one another. Monsters obey live
wall/portal headroom, bounded steps and drops, and closing doors conservatively
reopen when a monster occupies their box. This is a standalone sight/chase
controller, not Doom's original thinker system. Combat is the next checkpoint.

## Execution and controls

The SDCC-produced 8051 executes all sight tests, movement choices, actor/body
collision, animation state, projection, sorting, wall clipping and pixel writes.
The host converts original WAD assets, loads initial records, supplies keyboard
input and captures/verifies the CPU-written state and framebuffer. It does not
advance monsters or provide their rendered positions or visibility.

Use the patched repository and the supplied current/ image:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-monster-pose.json
```

W/S moves, A/D strafes, arrow keys turn, Shift increases movement and Space/E
uses an unlocked manual door. Omit --pose to start at the ordinary map spawn.
Native actors advance while input is enabled, using the same fixed 35/25 tick
schedule as the player. Disabled input freezes controller/actor ticks. The host
preview cap is not a hardware speed claim. The original shareware IWAD is
required and is not bundled with the build.

## Behaviour and limits

Two zombiemen near the supplied pose wake when the player is within a 512-unit
box and an unobstructed horizontal sight segment. Four farther E1M1 monsters
remain dormant during the demonstration. Active monsters choose one of eight
chase directions every four controller ticks, move four units axially or three
per diagonal axis, and try axis sliding when blocked. Their facing follows
the selected direction. Animation cycles through A-D every eight ticks.

The same native collision query used by the player checks monster bodies with
16-unit radius, 56-unit height, 24-unit step and 24-unit maximum drop. It keeps
the floor under the whole box when a stopped actor straddles stairs. Resetting
to the centre-sector floor in that case caused a penetration that the independent
oracle caught during development; the final code retains the last accepted
whole-body floor instead. Actor queries preserve the player's state and centre
cache. Player/body checks round outward conservatively. Monster-to-monster
bodies also block. Closing-door obstruction checks include dormant actors.

Sight is a horizontal segment at player-eye height against live collision
profiles, not the original sloped Doom sight algorithm. Bodies use conservative
boxes; chase has no path search. Awakened actors keep targeting the player even
if sight is later lost. They do not open doors. Current state is grounded for
all loaded actors and only the original E1M1 ground monsters are exercised.
Other IWAD monsters without all A-D rotations may be rejected by asset loading.
Monsters do not attack, take damage or die. Weapons, pickups, sound, HUD,
original Doom thinkers, gravity and real-time catch-up scheduling remain absent.

## Protocol and memory

The existing 78-byte boot record and main renderer schema are unchanged.
The additional CODE schema at F080h now identifies 20-byte actor records and
16-byte patch records. The packer still recognizes the preceding static 12-byte
record image when running that older supplied build.

DDR D0010h holds the count/header and D0020h holds up to 128 records:
int16 x/y, uint16 angle/kind, int32 temporary render depth, uint16 tics,
uint8 frame/awake, int16 whole-body floor and uint16 reserved. The CPU owns
runtime fields. E0010h holds 32 patch records per kind (four frames, eight
rotations); source index/opacity columns start at DDR 400010h and use explicit
32-bit native DDR reads. F6D0h retains sprite counts. Four uint16 counters at
F6E0h report total actor ticks, accepted moves, rejected moves and awake count.
Counters wrap modulo 65536; awake count describes the latest tick.

All four large projection/angle lookup tables now reside in simulated DDR.
The angle16 table retains all 2049 exact high words of the original full-width
table. Small sine and per-column view-angle tables remain in CODE. This makes
room for functionality in bank zero and is not a performance optimisation.
The final image occupies 61,010 code/constant bytes and 1,966 dynamic XRAM
bytes, plus the existing fixed cache/scratch, door states and mailboxes. The
observed stack high-water is D8h: 184/223 bytes used, 39 left. Monitor firmware
integration, hardware scanout and measured hardware timings remain unverified.
No monitor was flashed and no changes were committed or pushed.

## Captures and checks

current/doom-monsters-moving.mp4 is a convenient 12 FPS replay of 140 actual
CPU-written frames. current/doom-monsters-model-paced.mp4 is approximately
paced from the recorded CPU-model frame durations, about 23.06 seconds.
The latter includes native controller/actor work, rendering, RGB presentation
and flush. Worst model frame is 228.15 ms. These are the existing assumed
350.791 MHz CPU/flash/cache and 64-extra-clock DDR model, not hardware FPS.
The player holds position, retreats, then stops while the two monsters follow.
There are 196 actor ticks and 98 accepted moves. Native state, all moving
actor boxes, the player's pose, live door profiles and RGB conversion verify
on every completed frame. DDR invalid commands, busy-write hazards and stack
wraps are zero.

84 targeted tests pass across the recorded runs in validation/. The main run
has 82 passes and one skipped arithmetic check; the latter passes separately
with its assembler-path variable supplied. A separate full-renderer test puts
one real actor in an initially open door, keeps the player clear of that door,
and verifies that actor occupancy alone causes a closing door to reopen.
Other checks cover actor wall/headroom/step/drop limits, player-state isolation,
sight in both directions through live portals, body blocking, all four animation
frames, dormant monsters, independent per-frame geometry, original transparent
pixel sampling, rotation consistency, the 310-frame door sequence, HTTP/MJPEG,
cache/private pointers, DDR and arithmetic. There is no minimum-FPS assertion.
