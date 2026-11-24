# Native 8051 Doom: visible static monsters

Updated 24 November 2026. Start with source/docs/doom-monsters.md.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Work remains uncommitted and unpushed. No monitor was flashed.

current/ contains the NEW native sprite image, CPU-written frames, walkthrough
preview, captures, memory reports and native timing. door-baseline/ preserves
the previous door-only image/captures. The old README is below for history.

Six original medium-skill E1M1 monsters are loaded. Static sprites have the
original eight viewing rotations, mirrored patches, transparency, native
projection/back-to-front ordering, sector lighting and wall silhouettes.
They do not walk, attack or collide with the player. No combat, sound or HUD.

The image and 70-frame walk use real 8051 instructions and MCU_DC DDR. Host
code supplies input/assets and captures/verifies results. This is not a host
render. Preview plays at 12 FPS; native CPU-model timings are separate.
67 targeted checks pass and one is skipped; see validation/ and documentation.
The initial oracle failure in the regression log is corrected by the passing
independent oracle run, which accounts for actual floor/trigonometric values.

Apply doom-ddr.patch to the exact base in a separate checkout. For keyboard
preview, use scripts/doom_play.py with --out pointing to current/, your original
shareware doom1.wad, and --pose examples/doom-monster-pose.json.
The WAD, decoded WAD sprite assets and proprietary SDK are not bundled.

## Historical door-only checkpoint

# Native scaler walkthrough: doors and keyboard control

Current priority is functionality, not a 25 FPS target. Read
source/docs/doom-doors.md for current scope and run instructions.
Repository https://github.com/awto-au/awto-ddc
Base 505a3fd65de77f1ea2a50f7debed5909fe206e40
Branch work/doom-ddr-sim, not pushed. Apply doom-ddr.patch with git apply --index.
source/ contains all changed files, tests, generators and licensed Doom8088
subset. Existing repository files are required; this is a patch/distribution
of the current work, not an entire repository checkout.

WHAT WORKS
Native W/S forward/back, A/D strafe, arrows turn, Space/E use a door, Shift
faster movement, through a local keyboard preview page. Live MJPEG/VLC output
uses actual CPU-written framebuffer pixels. The host only supplies input,
loads assets, captures and independently checks the completed native state.
Normal unlocked manual doors open, wait and close; raise/stay doors stay open;
use can reopen a closing door, and player obstruction makes it reopen safely.
World ceiling changes update every collision portal too.

Still a standalone controller/render prototype. Monsters, combat, pickups,
keys, tagged triggers, original Doom thinkers/physics, sound and HUD are not
implemented. Door obstruction is conservative and checks only the player.
The controller still uses fixed 35/25 ticks per rendered frame, not an
independent real-time catch-up scheduler. No monitor was flashed.

IMPORTANT RENDERING CORRECTION
The previous conditional back-sector pointer assignment lost its private DDR
tag in compiled code, read XRAM zeros and treated open portals as closed.
That caused black doorway views and under-rendering. The new explicit-branch
assignment preserves the tag and fixes those views. Earlier renderer/walking
FPS claims are invalidated for the corrected renderer. Older scene movies
and timing claims are omitted here; unaffected math/DDR/stack baseline
records remain. The original full-width angle table's unused low words and
unused angle32 entry point were removed to fit the gameplay code in bank zero;
all 2049 angle16 values are checked for exact equivalence.

CAPTURES
current/ is the corrected 60x128 binary, map, memory/config reports, native
frames, poses, door states and full CPU-model timing. The 310-frame script
starts beside a real E1M1 door, opens it, enters the doorway, triggers one
obstruction reopen, leaves, turns around and lets it close. There are 434
native controller ticks and 80 height updates. All player poses, collision
profiles and RGB conversion checks pass with no invalid DDR commands,
busy-write hazards or PUSH wraps.

current/native-door-model-paced.mp4 is approximately paced from the CPU-model
frame durations (37.96 seconds). current/native-door-walkthrough.mp4 replays
the same captures at 25 FPS (12.4 seconds) for a shorter preview; it does not
claim native/hardware 25 FPS. The corrected run's worst CPU-model frame is
205.16 ms. No minimum-rate gate or optimization claim attaches to this phase.
The model remains 350.791 MHz, 3:1 CPU/flash, assumed shared flash-cache
geometry including MOVC reads, 32 MiB DDR, 64 extra clocks per DDR command and
SDK-default MOVX stretch. Real MPAGE wiring, bus behavior/contention, IRQs and
scaler scanout still need hardware verification.

KEYBOARD PLAYBACK
After applying the patch, run from the repository root:
  python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad     --pose examples/doom-door-pose.json
Then open http://127.0.0.1:8099/ on that computer, or open /stream in VLC.
For the normal map spawn omit --pose. The delivered current/ includes CODE
table data in tables.json, so SDCC/intermediate table binaries are not needed
to run this image. Python/numpy/Pillow and gcc for the simulator are required.
No original IWAD, preloaded asset RAM, proprietary SDK or compiler binary is
bundled. The user's original shareware doom1.wad is required.

VALIDATION
119 targeted tests pass, plus all 297 opcode/stretch cases, timers and dual
DPTR checks. Tests cover door range/front side/occlusion, waiting/closing,
raise-stay, use edges/manual reversal, body obstruction, passability/headroom,
forced DDR-cache aliasing, corrected nonblack doorway views, >255 capture
frames, HTTP input, JPEG/MJPEG, invalid input and clean stopping. A separate
live test decoded 25 actual MJPEG frames into H.264 with FFmpeg from a build
directory having no intermediate table binaries (live/). Tests no longer
assert a minimum FPS. Code/constants occupy 59022 bytes; dynamic XRAM is
1747 bytes, fixed cache/scratch+door states 4400 bytes plus mailboxes, within
8 KiB MCU XRAM. Stack high-water D5h uses 181/223 bytes, leaving 42.

Source licences and notices are retained. results/ and stack-bench/ contain
unaffected older low-level fixtures, not current gameplay FPS measurements.

VS CODE HANDOFF
Read source/docs/doom-vscode-handoff.md for laptop setup, exact patch base,
running the supplied image and the next functionality-first checkpoint.
This update adds the handoff only; the native image and test results are unchanged.
