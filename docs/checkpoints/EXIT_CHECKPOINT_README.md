# Native 8051 Doom: original level exit activation

Updated 24 November 2026. Start with source/docs/doom-exits.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Changes remain uncommitted/unpushed. No hardware was flashed.

Format 9 adds normal/secret use exits (11/51), native switch texture change,
a native EXIT banner and latched completion. Gameplay freezes after exit:
movement, actors, combat, projectiles, pickups, keys and door/button timers
stop. Rendering continues. The final suite passes 199 tests with no skips;
logs are in validation/. All game decisions/pixels remain 8051 instructions.

The recording uses original E1M1 exit linedef 330 without scene edits. The
supplied pose starts in its exit room. It walks toward the existing switch,
uses it at frame 20 and sends movement/turn/use/fire input for another 20
frames. All completed frames remain identical. This is an exit-room demo,
not a claimed full-level walkthrough from spawn. Completion is kind 1,
source 330, accepted once; health/ammo remain 100/50.

This checkpoint stops at completed-level state. It does not load another
map, implement original intermission statistics or episode routing. Stop
and rerun to start a fresh session. Larger original maps still exceed the
512-linedef bound. It is not a complete Doom port.

current/ has the new complete firmware, 41 native frames, state/timing
records and a silent model-paced video. Model timing is not measured
hardware FPS. The previous tagged-switch image/capture remains in
switch-baseline/ and SWITCH_CHECKPOINT_README.md. Other baselines remain
historical; the longer movie remains a separate earlier deliverable.

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together. The BIN is the complete 128 KiB two-bank
executable. The IHX alone is insufficient. Hardware memory/register/
scanout integration remains unverified. The patch includes its DDR
simulator header; clean exact-base restore, identical native rebuild,
fresh simulator compilation and original exit activation were checked.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-exit-pose.json
No --scene is required. W/S moves, A/D strafes, arrows turn, F/Ctrl fires,
and Space/E uses the exit. At death/completion stop and rerun. The original
IWAD, decoded asset RAM and proprietary SDK are not bundled. This archive
holds changed source, not a full repository. Read the handoff for setup.

Intermission/next-map flow, larger maps, weapons/armor, other trigger types,
sound, restart and a real-time tick scheduler remain future work.
Functionality precedes FPS optimisation.
