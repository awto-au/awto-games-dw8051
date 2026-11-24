# Current checkpoint: native ranged attacks and fireballs

Updated 24 November 2026. Read [doom-projectiles.md](doom-projectiles.md) first.
Soldiers shoot from range; imps throw visible balls that can be dodged and
hit walls/player bodies. The executable now uses two native code banks.
Keep current/doom_renderer.bin, doom_renderer.ihx and banking.json together.
Use examples/doom-fireballs-pose.json for the recorded imp encounter. All game
and render decisions remain native; no monitor was flashed or source pushed.
Next work includes pickups/keys and broader gameplay before FPS optimisation.
Historical checkpoint details below have older image/protocol requirements.

# Current checkpoint: native soldier ranged attacks

Updated 24 November 2026. Read [doom-ranged.md](doom-ranged.md) first.
Soldiers now fire deterministic hitscan attacks at range, with native windup,
recovery, live wall/range checks and pain/death interruption. Imps retain melee.
Use examples/doom-fireballs-pose.json for interactive play. The current checkpoint
has 98 unique passing tests and a 130-frame fight ending with two kills,
70 health and 41 rounds. Source remains uncommitted/unpushed; no hardware was
flashed. Functionality before FPS optimisation remains the goal. Earlier
checkpoint sections below contain historical behaviour, figures and counts.

# Historical checkpoint: native pistol/contact combat

Updated 24 November 2026. Read [doom-combat.md](doom-combat.md) first.
The native image now supports F/Ctrl firing, ammo, player/monster health,
pain/death, corpse pass-through and close-range monster attacks. Original
weapon patches and a small HUD are CPU-drawn. Use examples/doom-combat-pose.json
for the recorded fight. 90 tests pass. Source remains uncommitted/unpushed;
no hardware was flashed. Next work is broader gameplay, including ranged
attacks/projectiles and pickups, with functionality before FPS optimisation.
Historical checkpoint details below have older protocols and limitations.

# Current checkpoint: native monster chase

Updated 24 November 2026. Read [doom-actors.md](doom-actors.md) first.
Monsters now wake on native sight checks, animate A-D, chase the player and
respect wall/body/door collision. A stopped monster retains the whole-body
floor on stairs. The next checkpoint is native combat, health and attacks.
Use examples/doom-monster-pose.json beside the two visible zombiemen.
Functionality still takes priority over FPS. Historical checkpoint details
below have older memory figures, limitations and validation counts.

# Current checkpoint: static monster sprites

Updated 24 November 2026 after the original handoff below. Read
[doom-monsters.md](doom-monsters.md) first. The native image now displays
original static monsters with transparency, view rotation and wall clipping.
The next checkpoint is native actor state/behaviour and combat; functionality
still takes priority over FPS. Use examples/doom-monster-pose.json to start
beside the two visible zombiemen. The historical handoff below describes the
previous door-only checkpoint and its older validation/memory figures.

# Doom scaler project: VS Code handoff

Updated 24 November 2026. Continue functionality first. The user explicitly
deferred the 25 FPS target until the game works.

## Restore the work on a laptop

The archive is a patch distribution, not a complete repository checkout.
Its changes have not been committed or pushed. Cloning the repository alone
will not retrieve this work. Keep any existing checkout and its local edits;
use a separate checkout for the following commands.

```sh
git clone https://github.com/awto-au/awto-ddc.git awto-ddc-doom
cd awto-ddc-doom
git switch -c work/doom-ddr-sim 505a3fd65de77f1ea2a50f7debed5909fe206e40
git apply --check /absolute/path/to/extracted/doom-ddr.patch
git apply --index /absolute/path/to/extracted/doom-ddr.patch
code .
```

Authenticate with your existing GitHub access if necessary. Use Git Bash or
WSL for these shell examples on Windows. Open this folder in the official
OpenAI Codex extension and sign in with the same ChatGPT account and workspace.
The desktop app and IDE extension can share active chats for the same project.
This handoff also works if the mobile Work conversation is not in the IDE's
chat list. Do not assume the cloud workspace filesystem is the laptop's disk.

Prompt for the IDE agent:

> Read docs/doom-vscode-handoff.md and docs/doom-doors.md. Continue the native
> DW8051 Doom scaler prototype. Get gameplay working before FPS optimisation.
> Preserve the actual 8051 execution and simulated DDR register interface;
> host-side rendering, physics or arithmetic must not substitute for the CPU.
> Inspect local instructions and the current diff before editing. Do not flash
> monitor hardware or push changes as part of this handoff.

## Run the supplied image without rebuilding firmware

Install Python 3, numpy, Pillow and a C compiler (gcc for the simulator).
Use your legally obtained original shareware doom1.wad; it is not bundled.
Run from the patched repository root:

```sh
python scripts/doom_play.py --out /absolute/path/to/extracted/current --wad /absolute/path/to/doom1.wad --pose examples/doom-door-pose.json
```

Open http://127.0.0.1:8099/ in a browser on that computer. W/S move,
A/D strafe, arrows turn, Shift moves faster, Space/E uses a door.
VLC can open http://127.0.0.1:8099/stream. Omit --pose for the normal map
spawn. CODE table data is embedded in current/tables.json, so running the
supplied image does not require the SDCC build tree. Native Windows without
a compatible gcc setup is unverified; WSL provides a Linux development route.

## Current implementation and limits

* Real SDCC-produced 8051 opcodes execute in the fast simulator, with a
  32 MiB DDR backing store reached through the simulated MCU_DC interface.
  The MCU has an 8 KiB XRAM model. Scaler scanout is not simulated.
* E1M1 BSP wall rendering, flat floors/ceilings/sky, collision, native input,
  manual unlocked doors (specials 1 and 31), waiting/closing, use-edge handling
  and conservative player obstruction reopening are implemented.
* The host loads assets, sends input, reads CPU-written framebuffer pixels and
  validates results. It does not render or perform game physics for the CPU.
* This is a standalone controller/render prototype. Monsters, sprites/combat,
  pickups, keys, tagged triggers, original Doom thinkers/physics, sound and
  HUD are still missing. Do not describe it as a complete Doom port.

Read docs/doom-doors.md for current scope, build/run commands and caveats.
Build tooling is scripts/doom_renderer.py; interactive preview is
scripts/doom_play.py. Native movement and door code is in fw/doom/.

## Verification and timing

The latest saved validation has 119 targeted passing tests, plus all 297
opcode/stretch cases and timer/dual-DPTR checks. The 310-frame door script
checks 434 native controller ticks and 80 door height updates. It includes
walking through an open door and obstruction reopening. No invalid DDR
commands, busy-write hazards or PUSH wraps occurred in that run.

A critical private-DDR generic-pointer bug previously made open portals look
closed: a conditional expression lost the pointer tag and read zeroed XRAM.
The source preparation now uses explicit branches. Earlier renderer and
walking 25 FPS claims are invalid. The corrected scene's worst model frame is
205.16 ms, about 4.87 equivalent FPS for that frame, not an average or measured
hardware speed. The model assumes a 350.791 MHz CPU and a particular flash/cache
and DDR command timing. Hardware wiring, contention and scanout remain unverified.

current/native-door-model-paced.mp4 uses approximately model-based pacing;
current/native-door-walkthrough.mp4 is a 25 FPS replay for convenient viewing.
Its playback rate is not the native achieved frame rate.

## Next development checkpoint

First reproduce the supplied interactive image and inspect the native state
and captures. Then add the next small gameplay feature, starting with native
map-thing loading and visible static sprites before actor behaviour/combat.
Keep addresses and game state in the DDR model, test actual CPU-written
results against an independent oracle, and retain the door/collision regression
checks. Do not introduce a minimum FPS assertion at this stage.

Rebuilding needs the project's awto-sdcc fork and its runtime/linker setup;
the compiler binaries and IWAD are intentionally absent from this package.
Consult the existing build documentation rather than assuming stock SDCC
produces the same image. The saved tests describe the last code validation;
this handoff update changes documentation only.
