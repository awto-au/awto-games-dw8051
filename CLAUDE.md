# awto-games-dw8051

Global rules apply (`~/.claude/CLAUDE.md`). Repo specifics:

- Native 8051 Doom on the DW8051 sim; origin: awto-ddc doom-ddr-sim work. Start with README.md and docs/doom-vscode-handoff.md.
- Public repo (Dan, 2026-11-25). Approved for public hosting (Dan, 2026-11-25): the unmodified shareware doom1.wad, verbatim lumps, decoded assets, rendered frames / movies / images. Never commit registered or Doom II WADs, game ROM data (Atari / Namco) or proprietary SDK/vendor bytes.
- Pac-Man, Asteroids and Scope 2 are awto-ddc extra apps in a separate arcade image: `./arcade.py build|sim|budget`, `docs/arcade-image.md` (bank pins, budget, Doom bank plan). Packing Doom into the same flash is open work (plan + issues there); test on the `test` unit in awto-ddc `scripts/devices.json` only.
- Builds only through `ddc/dev.py` (awto-ddc submodule: `git submodule update --init ddc`); `arcade.py` is the one entry, `scripts/arcade_*.py` are its internal modules.
