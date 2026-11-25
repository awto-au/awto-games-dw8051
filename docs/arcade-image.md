# Arcade image

Pac-Man, Asteroids and Scope 2 as awto-ddc extra apps (awto-ddc#345, `ddc/docs/extra-apps.md`), in a separate firmware image. No hardware used, nothing flashed.

## Build / run
- `./arcade.py build` = shape data (`scripts/gen_asteroids.py --fallback`, own outlines) + `ddc/dev.py build --extra-fw fw/games --tag arcade`; `--release` = release layout, tag `arcade-rel`.
- `./arcade.py sim [--game NAME]` = every app in the firmware simulator (`scripts/arcade_sim.py`): start by VCP 0xEB, run 8 s fw time, MENU quit, VCP 0 stop, debug-byte start / stop; sound on and muted (VCP 0x8D).
- `./arcade.py budget` = `docs/arcade-budget.tsv` (needs the dev build last; the release build is optional).
- Default awto-ddc image: untouched (submodule pin `28e1196f`; `--extra-fw` off compiles the hooks out).
- Needs `git submodule update --init ddc` (pass `--reference` to a local awto-ddc to save the clone).

## Apps (VCP 0xEB = 0x20 + index, order = source path)
| index | app | source | state |
|---|---|---|---|
| 0 | asteroids | `fw/games/asteroids.c` | attract demo, autopilot ship |
| 1 | pacman | `fw/games/pacman_classic.c` | recorded demo, 8 steps/s, sound |
| 2 | scope2 | `fw/games/scope_saver2.c` | oscilloscope screen |
- Keys: MENU ends the app (`ARC_KEY_QUIT`, `fw/games/arcade.h`); the demos take no other input, other keys are ignored; POWER is the framework's.
- Ported from the screensavers (awto-ddc `723dc3df^`): `_AWTO_SAVER_*` guards gone, `AwtoAppFeed` for the raw watchdog clears, `AwtoAppScreenBegin` for the screen takeover (the stop path closes it), `AwtoAppTurn` / `AwtoAppGlyph` for the Rotate 180 tile turning, `saver_canvas.c` restored (`AwtoScTile` over `AwtoAppGlyph`, `ArcOsdMap1` = the removed `AwtoOsdMap1`).
- Pac-Man pacing: 4 sub-steps per 125 ms step with `AwtoAppMs` (was the saver loop); Asteroids and Scope 2 keep their own 40 ms frame schedule inside `step`.
- Sync-log pushes of the savers (E9 args 0x73..0x75, 0x7B..0x7D, 0x90..0x92) dropped: the framework logs start / stop (line E9 0x79).
- Sound: `fw/games/arcade_snd.c` = priority / loop / resume sequencer over `AwtoAppSoundTone` (tracks from `scripts/pacman_sound.py`, `arcade_snd_data.inc`). Honours user mute. Limits: awto-games-dw8051#2.

## Pins (`#pragma place bank(N)`, arcade image only)
- Pac-Man data + readers: bank 6 (`gen_pacman_classic.py` `PACMAN_BANK`; not bank 12: link gate gptr_const_xbank).
- Asteroids, all code + data: bank 8 (`gen_asteroids.py` `CODE_BANK`).
- Scope 2 + sound sequencer: bank 10 (`gen_scope2.py`, `pacman_sound.py`).
- Why pins, not groups: the packer picks a group's bank before the pins are applied; the 26 KB Pac-Man group landed in a bank without room ("no room for _g_pcDeltaA").
- Why these banks: bank 6 is empty in the default image (4.4 KB used since the savers left), bank 8 had Asteroids before, bank 10 has the most room left; in the release layout banks 6 and 8 keep the pins and the image still ends at bank 10.
- Pins hold for dev and release layout; `arcade_budget.py` fails when a game chunk sits outside its pinned bank.

## Bank budget (`docs/arcade-budget.tsv`, dev layout, 2026-11-25, awto-ddc `28e1196f`)
| bank | used B | free B | games |
|---|---|---|---|
| 6 | 48,261 | 7,035 | Pac-Man 43,784 |
| 8 | 49,123 | 6,173 | Asteroids 16,205 |
| 10 | 38,173 | 17,123 | Scope 2 8,973, sound 1,684 |
| 12, 13 | 33,367 / 32,872 | 21,929 / 22,424 | canvas 1,009 (bank 12), apps hooks 1,143 (banks 5, 12, 13 + stubs) |
- Capacity per bank 55,296 B (64 KiB - common 0x2800); bank 9 less the 8 KiB message block. Other banks: unchanged from the default image (`base` column).
- Game chunks (code + const + local stubs): Pac-Man 43,808 (code 2,183, const 41,601), Asteroids 16,229, Scope 2 8,989, sound 1,764, canvas 1,009, apps 1,143.
- XDATA: pool free 286 B (default image 1,249 B); game slots: Asteroids 515, canvas 228, Scope 2 188, Pac-Man 10, sound 10, apps 9. Window 0xE780..0xF6D0: 3,807 B free.
- IRAM: 5 B free direct, stack 128 B, 123 B data; identical to the default image (measured once, `fw_ram_report`).
- Release layout (`arcade.py build --release`): 11 banks (720,896 B), banks 0..2 and 5 almost full.

## Simulator results (`./arcade.py sim`, default dev image, sim machine cycles, 8 s fw time per run)
| app | sound | progress | passes | cycles / pass |
|---|---|---|---|---|
| asteroids | on | 63 game steps | 7,156 | 49,855 |
| asteroids | muted | 63 game steps | 9,976 | 26,331 |
| pacman | on | 256 sub-steps | 8,022 | 49,671 |
| pacman | muted | 256 sub-steps | 11,209 | 20,730 |
| scope2 | on / muted | 200 / 200 frames | 5,631 / 5,717 | 67,218 / 66,156 |
- Idle loop (no app, paced): 23,557 cycles / pass. A running app free-runs the loop (`AwtoLoopBusy`), so the idle value is no floor for the app rows.
- Sound on adds ~23 k cycles / pass: the blocking amp / DVC waits of every note (#2).
- Display Rotate 180: Scope 2 115,855 / 115,098 cycles / pass (turning the 2-plane tiles); Asteroids 52,786 / 28,015; Pac-Man 49,761 / 20,736.
- Release image: same ranges (Asteroids 50,757 / 26,441, Pac-Man 50,235 / 20,620, Scope 2 66,666 / 65,541).
- Per run: start by VCP, MENU stops it, scale-up off after the stop, VCP 0 stops, debug byte starts / stops: all pass (`tmp/arcade_sim/arcade_sim.tsv`). Snapshots show the Pac-Man maze with ghosts, the Asteroids field with HUD and info overlay, the Scope 2 trace.
- Framework check `ddc/scripts/apps_sim.py` runs only against the example app (`hello`): passes on the example build.
- Gates: `link`, `isr`, `regs` pass; `magic` lint 0 findings and `poke_loops` 0 unbounded loops when run by hand (the gates themselves fail for a root outside the awto-ddc tree: awto-games-dw8051#3).

## Doom in the same flash (plan, not implemented)
- Doom format-10 image = 196,608 B = 3 whole 64 KiB banks; non-0xFF 64,549 / 64,512 / 64,558 B. Banks 1 and 2 differ from bank 0 only inside the overlay window 0x5000..0x701C (5,654 B and 8,107 B): unique content 78,310 B.
- Doom's own common is 0..0x5000 (awto: 0..0x2800), identical in the three banks, so a Doom bank is a complete 64 KiB window, not an awto bank: it carries Doom's bytes at 0..0x2800 and cannot be called through awto bank stubs.
- Placement: release arcade image ends at bank 10 (11 banks), so Doom takes banks 11, 12, 13; bank 14 spare; bank 15 NVRAM / manifest (`ddc/docs/flash-layout.md`). The dev layout fills all 15 banks: no room, release layout only.
- Open (awto-games-dw8051#1; unit checks: #4):
  - Hand-off: bank register 0xFFFF is the register Doom's simulator model uses, unverified on the unit. The first instruction after the select executes from the Doom bank at the same address: needs a landing pad in the Doom image at the awto call-site address (reserved ABS area) and the mirror pad for the way back.
  - Doom's bank numbers 0 / 1 / 2 are literals (`fw/doom/projectile_bank.asm`, `mov a,#N`): relocate to 11 / 12 / 13 with an assembler define.
  - While Doom runs, the vectors 0..0x53 are Doom's: no awto Timer2 / debug-link ISR, no watchdog feed (bite 586 ms); Doom needs its own feed.
  - Data: every map needs a DDR scene (E1M1 406 blocks = 1,662,976 B, E1M9 603 blocks = 2,469,888 B, zipped 334 KB .. 612 KB) against 2 spare banks (131,072 B) and a 1 MiB flash: the scene has to come from the host or other storage; the simulator loads it before boot.
  - Frame buffer: Doom's DDR layout (A6010, 140010, 160010, 800010) must not collide with the scaler's M-domain use of the DDR.
- Not implemented here: the mapping cannot be tested without the unit (and a hand-off / data path nobody has verified), and the combined image would need a Doom rebuild.
