# Native 8051 Doom: soldiers shoot at range

Updated 24 November 2026. Start with source/docs/doom-ranged.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Changes remain uncommitted and unpushed. No monitor was flashed.

current/ contains the NEW ranged-combat firmware, 130 CPU-written frames,
model-paced and convenient replay videos, state/timing logs and memory reports.
The preceding pistol/contact checkpoint is retained in combat-baseline/.
Earlier captures remain under chase-baseline/, static-monster-baseline/
and door-baseline/. Read their checkpoint files as historical records.

Soldiers use deterministic hitscan attacks within a 512-unit box, with an
8-tick windup, 27-tick recovery and live wall/range/height checks at impact.
Pain or death cancels a pending shot. Imps keep their close-range attack.
Native pistol, ammo, health, HUD, collision, doors and corpses remain working.
F/Ctrl fires. At death, stop and rerun. There is no sound, pickup, projectile,
restart button or original Doom thinker system. This is a standalone prototype.

All decisions and pixels run as 8051 instructions through simulated DDR.
Host code loads assets/input and checks/captures results. 98 unique tests
passed; validation logs document the separately enabled arithmetic check.
The 130-frame original E1M1 fight ends with two kills, health 70 and ammo 41.
Its model durations total 20.98 seconds, with a worst frame of 248.08 ms.
These are assumed CPU-model timings, not measured hardware FPS.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-ranged-pose.json
Use examples/doom-ranged-demo.json for the recorded fight. The original
shareware IWAD, decoded asset RAM and proprietary SDK are not bundled.
The archive contains changed source, not a complete repository. Read the
handoff for compiler/linker/runtime requirements. Functionality comes before
FPS optimisation. Next work includes imp projectiles and pickups.
