# Games: Pac-Man, Asteroids, Scope 2 (imported from awto-ddc)

- Imported 2026-11-25 from awto-ddc (`scripts/`, `tests/`, `fw/test/`, `docs/`, `tools/pacman_osd/`). awto-ddc still compiles them into its default image (screensaver feature), so the originals stay there.
- Firmware sources: `fw/games/` (`asteroids.c`, `pacman_classic.c`, `scope_saver2.c` + generated `.inc`). They build only inside awto-ddc's SDK tree (`fw/test/` there); paths here were renamed to `fw/games/`.
- Host tools: `scripts/asteroids_*.py`, `pacman_*.py`, `scope2_*.py`, `gen_*.py`; tests `tests/test_{asteroids,pacman,scope2}_*.py`.
- Dependency on awto-ddc helpers (not copied; `$AWTO_DDC_SCRIPTS`, default `/mnt/2tb/git/awto-ddc/scripts`): `_log`, `osd_render`, `ddc_sim`, `osd_gfx`, `audio_sim`, `settings_cli`, `rtd_i2c_bridge`, `i2cbus`, `dbg_link`, `card_shot`, `osd_vlc`.
  - Tests: `tests/conftest.py` adds its `scripts/`. Scripts: `PYTHONPATH=$AWTO_DDC_SCRIPTS`; `scripts/_repo.py` here shadows awto-ddc's so ROOT is this repo.
- Asteroids ROM data is never committed (`asteroids_data.inc`, ROM zips): see `asteroids.md`.
- Open: pack Doom + these games into the monitor's whole flash and test together (not started).
