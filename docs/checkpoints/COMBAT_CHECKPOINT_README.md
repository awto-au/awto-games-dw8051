# Native 8051 Doom: pistol and contact combat

Updated 24 November 2026. Start with source/docs/doom-combat.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Work remains uncommitted and unpushed. No monitor was flashed.

current/ contains the NEW combat image, 130 CPU-written frames, both
model-paced and convenient replay videos, state/timing logs and memory reports.
Earlier images/captures are retained under chase-baseline/,
static-monster-baseline/ and door-baseline/. Historical validation has older
counts and limitations; current validation is combat-regressions.log.

F/Ctrl fires the pistol. Native rules include 50 rounds, cooldown, nearest
visible target selection, health, pain/death animation, corpse pass-through
and close-range monster attacks. The original pistol patches, crosshair,
health/ammo digits and damage border are CPU-drawn. At zero health movement
and firing freeze; stop and rerun to start a fresh session. There is no reload,
sound, ranged monster attack, projectile, pickup or original Doom thinker
system. This is a standalone deterministic combat prototype.

All decisions and pixels run as 8051 instructions through simulated DDR. Host
code loads initial assets/input and checks/captures results. It does not aim,
apply damage or render. 90 tests pass with no skips; native counters and pixels
are independently verified. Source and images were not flashed or pushed.

The model-paced movie is about 24.43 seconds for 130 frames. Two original
monsters inflict 20 damage; nine shots use nine rounds and kill both. Final
health is 80 and ammunition 41. Worst assumed CPU-model frame is 292.41 ms,
not measured hardware FPS. The convenient preview replays at 12 FPS.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-combat-pose.json
Use examples/doom-combat-demo.json with scripts/doom_renderer.py for the
recorded fight. The original shareware IWAD, decoded sprite/weapon RAM and
proprietary SDK are not bundled. See the handoff for compiler/linker/runtime
requirements and the current CODE schema marker/address change.
