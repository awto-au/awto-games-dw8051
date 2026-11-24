Current update: native ranged attacks and fireballs are implemented; read [doom-projectiles.md](doom-projectiles.md).

# Native pistol and contact combat

Historical checkpoint. The latest firmware also has native soldier ranged
attacks; read [doom-ranged.md](doom-ranged.md) for current behaviour and capture.

24 November 2026. The standalone 8051 prototype now has a pistol, ammunition,
player/monster health, nearest-target hits, pain/death animations, nonblocking
corpses and close-range monster attacks. The CPU draws the original pistol
patches, muzzle flash, crosshair, health/ammo digits and damage border. This
continues the prototype; it is not the original Doom thinker/combat system.

## Play

Apply the supplied patch to the exact repository base, then run the supplied
current/ image with the original shareware IWAD:

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-combat-pose.json
```

W/S moves, A/D strafes, arrows turn, Shift increases speed, Space/E uses an
unlocked manual door and F/Ctrl fires. The original map spawn is available by
omitting --pose. Brief use/fire taps are independently latched until the next
native input sample. Held fire repeats at the native cooldown. The browser
shows health, ammo and kills from the CPU's state, and VLC can open /stream.
At zero health movement/firing and actor ticks freeze. Stop and rerun the
simulator to start a fresh session; there is no in-game restart or reload.

## Native rules

The player starts with 100 health and 50 rounds. One shot consumes one round,
sets a three-tick muzzle flash and a seven-tick cooldown. The CPU transforms
actor coordinates with its sine/cosine/fixed-point routines. It selects the
nearest live target with positive depth no greater than 1024, lateral offset
within 16 units and an eye-height intersection with its 56-unit body, then
checks live wall/portal sight. Misses consume ammo. A hit does 20 damage and
interrupts an attack with pain or death. Original map soldiers have 20 health
and imps 60 in this prototype. No spread, randomness or original Doom weapon
balance is claimed.

Walk frames are 0-3; attack windup/recovery are 4/5; pain is 6; death progresses
through 7-11 and leaves a corpse. Original soldier sprites use pain G/death H-L;
imps use pain H/death I-M. Mirrored view rotations and transparent posts remain
native-rendered. Dead bodies no longer block the player, other actors or doors.

A nearby awake monster can enter an eight-tick attack windup within a 48-unit
box. At impact the CPU rechecks range, body-height overlap and live wall sight.
A successful contact attack does 10 player damage and shows a five-tick border.
Recovery lasts 27 ticks; the next attack also needs the locomotion timer to
reach its 32-tick check. These are deterministic close-range attacks for both
soldiers and imps. Projectile motion, ranged monster attacks and vanilla Doom
AI/rules are absent even where an original attack sprite depicts muzzle fire.

The HUD, weapon pixels, actor decisions, collision, hit selection, health and
ammo arithmetic, animation and RGB framebuffer conversion all execute as SDCC
8051 opcodes through the simulated DDR interface. The host packs assets,
loads initial state, supplies input, captures completed frames and verifies
results. It does not aim, apply damage, choose victims or render pixels.

## Protocol and memory

A CODE marker `D805`, version 3, is at FFF0h. Main schema words move from F000h
to FF00h; the extra actor/patch schema moves from F080h to FF80h and adds combat
version 2. The combat-state size word is at FF90h. The asset loader recognizes
the preceding schema locations for older images. The 78-byte boot record and
six-byte input record remain unchanged. Buttons bit 0 is use and bit 1 fire.

Actor records remain 20 bytes. The last uint16, formerly reserved, is now
health. E0010h holds 96 patch records per kind: 12 semantic frames with eight
view rotations each. Weapon patch metadata is at DDR 1D0010h; its source pixels
follow the other explicitly addressed sprite pixels. The exact sine quarter
wave (4096 bytes) now resides at DDR 1B0010h to make room for combat in bank
zero. Other large angle/projection tables were already in DDR.

The 22-byte native combat state at MCU XRAM F700h contains eight uint16 values
(health, ammo, shots, hits, kills, received damage, attack attempts, dead), four
uint8 values (cooldown, flash, hurt, spare) and a uint16 last-shot target ID.
F71Eh is a boot-time HUD-enable byte. Tests can hide the separate overlay pass
for independent world-render sampling; interactive play enables it. Small
views below 48 pixels tall omit the weapon/flash but keep digits/crosshair.

The 60x128 image uses 63,389 code/constant bytes and 2,023 dynamic XRAM bytes,
plus the established fixed caches, door states and mailboxes. Demonstration
stack high-water is DBh: 187/223 stack bytes used, leaving 36. No stack wraps,
invalid DDR commands or busy-write hazards occurred. Monitor integration,
actual MCU memory mapping/contention and scaler scanout remain unverified.
No monitor was flashed and no changes were committed or pushed.

## Capture and verification

current/doom-combat-model-paced.mp4 shows 130 actual CPU-written frames,
approximately paced from recorded model durations: 24.43 seconds. The convenient
current/doom-combat-preview.mp4 replays the same frames at 12 FPS. In the
original E1M1 scene two monsters hit the player, reducing health to 80. Nine
shots consume nine rounds and kill both monsters; remaining ammunition is 41.
The player then walks through their former blocking area. The four farther
monsters remain alive. Source commands and the initial pose are included.

Worst model frame is 292.41 ms under the existing assumed 350.791 MHz CPU,
shared flash/cache behaviour and 64-extra-clock DDR commands. This includes
native control/combat, world rendering, weapon/HUD, RGB conversion and flush;
it is not measured hardware FPS. There is no minimum-FPS test or 25 FPS claim.

90 tests pass, with no skips. Combat fixtures check nearest-target selection,
wall occlusion, misses, cooldown, empty ammunition, release/tap handling, pain,
death, corpse pass-through, contact damage, player death and frozen input.
An independent decoder checks every sampled original pistol pixel and HUD
numbers/crosshair. The host also verifies ammo+shots=50, hit/kill counts,
player health against damage, total lost monster health against hit damage
and dead-body count against kills for every captured frame. Existing actor,
310-frame door/obstruction, movement, HTTP/MJPEG, cache/private-pointer, DDR
and arithmetic checks pass. The browser input/status JavaScript passes syntax
checking. Logs are in validation/.

Remaining gameplay work includes monster projectiles/ranged attacks, pickups,
keys/tagged triggers, more weapons, sound, restart flow and a real-time tick
scheduler. Floors/ceilings/sky still use the earlier flat approximations. The
combat asset set currently accepts original E1M1 imps/soldiers; other monster
types are explicitly rejected instead of receiving incorrect animations.
