# Native 8051 Doom: soldier shots and imp fireballs

Updated 24 November 2026. Start with source/docs/doom-projectiles.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Work remains uncommitted/unpushed. No monitor was flashed.

current/ contains the NEW format-5 two-bank image, 127 CPU-written frames,
model-paced and preview movies, native state/timing and banking reports.
The intervening soldier checkpoint is retained in soldier-ranged-baseline/,
SOLDIER_CHECKPOINT_README.md, soldier-checkpoint.patch and soldier-validation/.
Its documentation, original examples and expanded tests are retained. Earlier
combat/chase/static/door checkpoints remain in the existing baseline folders.
The current full suite passes 104 tests with no skips; see validation/.

Soldiers retain deterministic 10-damage ranged shots and their sight/range/
height and interruption checks. Imps now launch visible fireballs which can
be dodged, hit walls/player bodies and explode. Decisions, fixed trajectories,
impacts, damage and all pixels execute on the simulated 8051. There are no
host-side gameplay or rendering substitutes. Native sine/cosine matches all
8192 original samples. The bounded eight-slot pool safely drops excess shots.

IMPORTANT: keep doom_renderer.bin, doom_renderer.ihx and banking.json together.
The BIN is the complete 128 KiB two-bank image; the IHX alone is insufficient.
The runner checks its hash and bank-zero bytes. Native trampolines switch and
restore banks. This uses the simulator's MOVX FFFF bank-selection model;
actual monitor-register integration remains unverified. The asset loader
also retains version-4 soldier-mask compatibility for the older image.

The model-paced movie is about 25.05 seconds for 127 frames. The player dodges
one fireball, gets hit by another, then kills the original E1M1 imp. Final
health is 90, ammo 42 and kills 1. One ball hits a wall and one hits the player.
Worst assumed CPU-model frame is 349.44 ms, not measured hardware FPS. The
convenient preview replays the same captures at 12 FPS. Sound, pickups and the
original Doom thinker system remain absent; functionality precedes FPS work.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-fireballs-pose.json
W/S move, A/D strafe to dodge, arrows turn, F/Ctrl fire, Space/E use a door,
Shift moves faster. examples/doom-fireballs-demo.json records this encounter.
The older examples/doom-ranged-* files retain the soldier demonstration.
At zero health stop and rerun for a fresh session. The original shareware
IWAD, decoded assets and proprietary SDK are not bundled. Read the handoff
for setup, current format requirements and next gameplay checkpoints.
