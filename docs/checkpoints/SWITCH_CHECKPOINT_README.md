# Native 8051 Doom: tagged door switches

Updated 24 November 2026. Start with source/docs/doom-switches.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Changes remain uncommitted/unpushed. No hardware was flashed.

Format 8 adds tagged switch specials 29/63/103/61. The 8051 activates all
linked door sectors, changes SW1 to SW2, consumes one-shot uses and resets
reusable buttons after 35 controller ticks. Range/front-side/wall checks and
use edges remain native. Zero/unmatched tags cannot broadcast. Keys, health,
ammo, fireballs, combat and existing manual-door behaviour remain enabled.
The final suite passes 184 tests with no skips; logs are in validation/.

E1M1 has no original supported tagged door switches: its exit remains
unsupported. The demonstration explicitly changes an existing corridor wall
into a reusable switch, with a tag linking it to an existing door sector.
Original geometry and original SW1STRTN/SW2STRTN artwork are used. All edits
happen before CPU boot. No host scene changes occur during play.

current/ holds the new firmware and 59 CPU-written capture frames. The
silent model-paced movie shows switch activation, its reset, and passage
through the linked door. Model frame durations total 8.91 seconds; MP4
playback adds quantization. These are not measured hardware FPS.
The previous key image/captures remain in keys-baseline/ and
KEYS_CHECKPOINT_README.md. Other baselines remain historical. The previously
requested long movie remains a separate earlier deliverable.

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together. The BIN is the complete 128 KiB native two-bank
image; the IHX alone is insufficient. Actual monitor register/scanout
integration remains unverified. The simulator DDR header is included in the
patch. Clean exact-base restore, identical native rebuild and a fresh
simulator switch activation were verified.

Apply doom-ddr.patch to the exact base in a separate checkout. Keyboard play:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad --pose examples/doom-switch-pose.json --scene examples/doom-switch-scene.json
Space/E presses the switch, arrows turn and W/S moves through the linked
door. A/D strafes, Shift speeds movement, F/Ctrl fires. At death stop and
rerun. The IWAD, decoded asset RAM and proprietary SDK are not bundled.
This is a changed-source archive, not a full repository; read the handoff.

This remains a standalone gameplay prototype, not original Doom thinkers.
Level exits, larger maps, other triggers, weapons/armor, sound, restart
flow and a real-time tick scheduler remain future work. Functionality
precedes FPS optimisation.
