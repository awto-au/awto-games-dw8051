# Native 8051 Doom: health and ammunition pickups

Updated 24 November 2026. Start with source/docs/doom-pickups.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Changes remain uncommitted/unpushed. No monitor was flashed.

The current format-6 image adds stim packs, medikits, health bonuses, ammo
clips and ammo boxes. Collection, capacity limits, wall/height checks,
sprite removal and HUD feedback execute on the 8051. Full-capacity items
remain available. Items collect once, do not block movement and cannot
revive a dead player. E1M1 has 19 supported original pickups. The final
suite passes 121 tests with no skips; logs are in validation/.

current/ holds the complete two-bank firmware, main medikit scene and
27.23-second model-paced movie. current/pickup-scenes/ retains all 279
native frames and input/state/timing records for three original E1M1 scenes:
health bonus 100 to 101, clip ammo 50 to 60, medikit healing 80 to 100 after
imp attacks. A later imp hit leaves 90. Scenes reset separately. The movie
is silent. Its playback timing is not a hardware FPS measurement.

The previous fireball image/capture is retained in fireball-baseline/ and
FIREBALL_CHECKPOINT_README.md. Earlier baseline folders remain historical.
The previously requested long gameplay movie remains a separate deliverable.

IMPORTANT: keep doom_renderer.bin, doom_renderer.ihx, banking.json,
tables.json and cache-config.json together. The BIN is the complete native
128 KiB two-bank image; the IHX alone is insufficient. Bank switching still
uses the simulator's MOVX FFFF model, not verified monitor register wiring.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-pickups-pose.json
Walk over items, W/S move, A/D strafe, arrows turn, F/Ctrl fire, Space/E use.
At death stop and rerun the simulator. examples/doom-pickups-demo.json
replays the medikit encounter. The original shareware IWAD, decoded asset
RAM and proprietary SDK are not bundled. This is a changed-source archive,
not a complete repository. Read the handoff for compiler/runtime setup.

This remains a standalone gameplay prototype, not original Doom thinkers.
Keys/tagged triggers, weapon/armor inventory, sound, restart flow and a
real-time tick scheduler remain future work. Functionality precedes FPS work.
