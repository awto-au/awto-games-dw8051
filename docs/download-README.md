# Doom DW8051 single download

Prepared 25 November 2026. Extract this ZIP completely before opening files.

This download contains the complete Doom work to date:

- source/: full current awto-ddc repository source snapshot with the Doom changes
  already present. No git clone or patch application is required.
- wads/doom1.wad: the original 4,196,020-byte Doom shareware Episode 1 IWAD used
  for this work. It contains E1M1-E1M9. No registered Doom or Doom II WAD was
  supplied, so those WADs are not in this download.
- translated/: all decoded graphics, palettes, original lumps, normalized map
  data, native DDR scenes for all nine maps, firmware and native captures.
- checkpoints/: the complete earlier source/firmware checkpoint archive expanded,
  including its patch, historical checkpoints, documentation and validation logs.
- previews/: the current two-minute native episode preview, earlier gameplay
  recordings and screenshots from this project.
- play.py: start any prepared map using the prebuilt native firmware.
- verify_download.py and download-manifest.json: verify every packaged file.

## Start a prepared map

Tested on Linux. Windows users can run these commands in WSL. The simulator
requires Python 3 and gcc on the computer. gcc builds its native simulator
library automatically on first use. The operating system, Python, gcc and SDCC
installations are external prerequisites, not files embedded in this archive.
The prepared maps already contain the compiled 8051 firmware, so SDCC is only
needed for rebuilding firmware and compiler-dependent tests.

From this extracted folder:

    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r requirements.txt
    python verify_download.py
    python play.py --map E1M1

Open the local address printed by the program, normally http://127.0.0.1:8099/.
Select another map with --map E1M2 through --map E1M9. To limit a session use
--frames 100. The preview is served locally and can also be opened in VLC at
http://127.0.0.1:8099/stream.

W/S moves, A/D strafes, arrows turn, F/Ctrl fires, Space/E uses, Shift increases
movement speed. Stop and restart after death or level completion.

The WAD is available for retranslation at wads/doom1.wad. Documentation in
source/docs/doom-translation.md explains the converter and compiler settings.
source/docs/doom-vscode-handoff.md provides the code-agent handoff. Rebuilding
uses the project's awto-SDCC compiler and compatible SDCC assembler/linker and
large-stack-auto support libraries; the earlier validation logs retain their
original build paths as historical records.

## Current state

All graphics and level data from the supplied shareware WAD have been translated.
All nine maps render using native 8051 code, including textured floors, ceilings
and sky. The previous implementation validation covers 211 unique passing checks
and 216 native frames across the nine maps. CPU-model timing is not measured
hardware performance. The video is a rotating-map preview, not a full playthrough.

The game port remains unfinished. Original lifts, stairs, damaging floors,
crushers, walk triggers, teleports, full weapons/armor/powerups, decorative thing
rendering, masked middle textures, full lighting/animation, sound playback,
intermission and campaign progression still need native implementations. These
features' original data is retained and audited. No monitor hardware was flashed.

Source and third-party licence notices are retained in their original folders,
including source/fw/doom/vendor/Doom8088/LICENSE. This is a download of this
project's available source, assets and results, not a completed Doom release.
