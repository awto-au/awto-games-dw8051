# Native 8051 Doom: animated monster chase

Updated 24 November 2026. Start with source/docs/doom-actors.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Work remains uncommitted and unpushed. No monitor was flashed.

current/ contains the NEW native actor image, 140 CPU-written frames,
model-paced and convenient replay videos, state/timing logs and memory reports.
static-monster-baseline/ retains the preceding static monster capture/image;
door-baseline/ retains the previous door-only checkpoint.

Monsters wake on native sight, animate original A-D walking frames, chase the
player and obey walls, portal heights and bounded steps/drops. Player and
monster bodies block one another. Monsters in a closing door make it reopen.
This is a standalone ground-actor controller, not the original Doom thinkers.
There are no attacks, damage, weapons, pickups, sound or HUD. Combat is next.

The CPU executes all actor decisions, collision, projection, pixels and RGB
conversion through simulated DDR. Host code loads assets/input and checks or
captures results. It does not move or render monsters. There is no hardware
FPS claim. The model-paced movie is about 23.06 seconds for 140 frames, with
228.15 ms worst model frame. The convenient preview replays at 12 FPS.
84 targeted tests pass across validation/actor-* logs (the main run's one
skipped arithmetic check passes separately with its assembler path supplied).

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard preview:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-monster-pose.json
Use examples/doom-monster-chase.json with scripts/doom_renderer.py for the
recorded idle/retreat/follow command sequence. The original shareware IWAD,
decoded sprite asset RAM and proprietary SDK are not bundled. See the handoff
for the awto-sdcc compiler and matching linker/runtime requirements.
