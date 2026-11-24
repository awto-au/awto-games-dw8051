# Native 8051 Doom: keys and coloured manual doors

Updated 24 November 2026. Start with source/docs/doom-keys.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Changes remain uncommitted/unpushed. No hardware was flashed.

Format 7 adds persistent blue/yellow/red card/skull inventory, coloured
manual locks, native HUD indicators and browser key/denial feedback. A
matching key unlocks its colour and is retained. Other colours fail.
Pickup contact/height/wall checks, health/ammo, fireballs, pistol combat,
manual-door movement and all game pixels still run on the native 8051.
163 tests pass with no skips; final logs are in validation/.

E1M1 has no original keys or coloured locks. The supplied demonstration is
an explicit initial test scene: it adds a blue card and sets an existing
door's use specials before CPU boot. The original geometry is preserved.
No host scene edits run during gameplay. The silent model-paced movie has
111 actual CPU-written frames: visible card collection, then denial,
collection, successful use and passage. Sessions reset between sections.
Timing is not measured hardware FPS. Skull inventory/locks are tested with
logic fixtures; the shareware IWAD lacks original skull artwork.

current/ contains the NEW complete two-bank firmware, main 86-frame door
capture, a 25-frame keycard capture and model-paced movie. The previous
pickups image/captures remain in pickup-baseline/ and
PICKUPS_CHECKPOINT_README.md. Earlier baselines remain historical. The
previously requested long video remains a separate earlier deliverable.

The patch now includes scripts/mcs51_ddr.h, accidentally omitted from the
previous patch while present in its source bundle. A clean checkout of the
exact base was patched, rebuilt to the identical full native image and
used to compile a fresh simulator and verify native lock denial.

IMPORTANT: keep doom_renderer.bin, doom_renderer.ihx, banking.json,
tables.json and cache-config.json together. The BIN is the complete 128 KiB
two-bank executable; the IHX alone is insufficient. Bank selection remains
the simulator MOVX FFFF model, unverified on monitor hardware.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-keys-pose.json --scene examples/doom-keys-scene.json
Space/E tries the locked door. Back up to collect the blue card, move
forward, release and press use again. W/S moves, A/D strafes, arrows turn,
F/Ctrl fires. At death, stop and rerun. The original shareware IWAD, decoded
assets and proprietary SDK are not bundled. This is a changed-source archive,
not a complete repository. Read the handoff for compiler/runtime setup.

This is a standalone gameplay prototype, not original Doom thinkers. Tagged
switches, broader maps, weapons/armor, sound, restart flow and a real-time
tick scheduler remain future work. Functionality precedes FPS optimisation.
