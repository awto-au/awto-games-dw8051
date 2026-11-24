# awto-games-dw8051

Global rules apply (`~/.claude/CLAUDE.md`). Repo specifics:

- Native 8051 Doom on the DW8051 sim; origin: awto-ddc doom-ddr-sim work. Start with README.md and docs/doom-vscode-handoff.md.
- Public repo (Dan, 2026-11-25). Never commit the Doom IWAD, decoded assets, frames/movies rendered from it, game ROM data or proprietary SDK/vendor bytes. `local/` (gitignored) holds the removed Doom-derived renders.
- Packing the doom image with pacman, asteroids and scope into the monitor's whole flash is open work; test on the `test` unit in awto-ddc `scripts/devices.json` only.
