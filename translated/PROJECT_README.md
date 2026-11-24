# Native DW8051 Doom: whole-episode graphics and level translation

Updated 25 November 2026. Read source/docs/doom-translation.md first.
Repository https://github.com/awto-au/awto-ddc
Patch base 505a3fd65de77f1ea2a50f7debed5909fe206e40.
Changes remain uncommitted/unpushed. No hardware was flashed.

The complete supplied Episode 1 WAD has been translated in one consolidated
pass: all nine E1M1-E1M9 maps, 968 patches, 54 floor/ceiling flats, 125 wall
textures, 14 palettes, all colour maps and every one of its 1,264 raw lumps.
Original weapon, monster, interface and intermission graphics are decoded with
coverage masks, offsets, rotations and mirroring. All map fields, things, tags,
line/sector specials, BSP, BLOCKMAP and REJECT data are retained and validated.
Doom8088's original 314-state graph and 49 thing definitions are also data in
the translation. The source project retains the original GPL notices.

Format 10 adds native perspective floor/ceiling texture sampling and original
SKY1 columns, 2,048-line collision maps, 32 doors, 32-bit switch target masks,
a use-action lookup table, and Demon/Spectre/Baron art and prototype behaviour.
A third native code bank contains HUD/plane/sky routines. The complete executable
is 196,608 bytes; keep the BIN, IHX, banking.json, tables.json and cache-config.json
together. IHX alone does not contain all native code.

Validation: 216 native frames across all nine converted maps, with
control input active, zero stack wraps, zero invalid DDR accesses and zero DDR
hazards. Palette output, collision geometry, native game-state accounting and
bank restoration passed. The whole regression run passed 210 tests. The final
translation run passed 12, including one subsequently added archive-reproducibility
test: 211 unique passing tests overall. Per-payload hashes and map record round
trips were checked. The exact-base patch restores all 169 changed/new files;
a clean rebuild produced the identical firmware and a fresh simulator loaded
converted E1M6. Logs are in validation/.

current/ has firmware, source maps, all nine native captures, the report, a
nine-level montage and a silent 2 minute 5 second episode preview. The video
uses simulated CPU-clock pacing, with captions. It is a rotating-map preview,
not a full playthrough or measured hardware performance. Historical checkpoints
remain under their baseline directories and *_CHECKPOINT_README.md files.

The separate doom-episode-one-translated.zip contains the full decoded asset
bundle, graphics contact sheets and native/E1Mx scene folders. The DPAK and
sparse DDR scene archives have deterministic bytes. Converted scenes load
without the original WAD:

    python3 scripts/doom_play.py --out /path/to/native/E1M6 --packed /path/to/native/E1M6

Alternatively run from current/ with --wad /path/to/doom1.wad --map E1M6.
W/S moves, A/D strafes, arrows turn, F/Ctrl fires, Space/E uses, Shift increases
speed. Stop and rerun after death/completion. To regenerate everything:

    python3 scripts/doom_translate.py --wad /path/to/doom1.wad --native /path/to/current --verify-native --frames 24 --out /path/to/output

The asset and level translation is complete for this supplied shareware WAD.
Full Doom gameplay remains unfinished: original sector thinkers, damaging
floors, lifts, stairs, crushers, walk triggers, teleports, full weapons/armor/
powerups, decorative thing rendering/behaviour, masked middle textures, full
vanilla lighting/animation, sound, intermission and campaign progression remain
unported. The Baron uses the prototype imp fireball routine/art. Original data
for unported features is preserved and unsupported actions/types are listed per
map. The supplied WAD does not include registered episodes or Doom II.
Hardware bank-register, memory and scanout integration are unverified.
Functionality precedes FPS optimisation.
