# Native Doom renderer on the DDR simulator

**Superseded renderer timing:** [the door/walkthrough milestone](doom-doors.md)
fixes a lost back-sector DDR pointer tag. Earlier renderer/walking FPS figures
below under-rendered open portals and must not be used for the corrected
renderer. Functionality now takes priority; no minimum FPS is enforced.
Arithmetic and DDR unit checks remain applicable.

Implemented 20 November 2026 against awto-ddc base `505a3fd`.

The latest milestone adds [native player movement and collision](doom-motion.md).
The 40x80 timings below describe the preceding renderer-only binary. With the
controller linked, the guarded stationary preset is 40x64; the 180-frame moving
workload reaches 25 FPS at 30x48. See the movement document for current results.

`scripts/doom_renderer.py` builds and executes a native MCS51 executable using
Doom8088's E1M1 BSP traversal, view projection, wall clipping and textured
column renderer. Python converts WAD assets into SDCC structures and preloads
DDR. All visible columns, indexed pixels and BGR888 palette conversion execute
as actual 8051 instructions. There are no host rendering or maths callbacks.

This is **renderer/controller bring-up, not a playable Doom port**. Scripted
native movement and static collision are integrated. Original Doom thinkers,
actors, sprites, sound and the HUD remain unimplemented. Floors/ceilings
and sky are flat colours. The selectable viewport defaults to 60x128. A 40x80 preset passes the
25 FPS rendering target in the current model. Previews expand to 480x256
with nearest-neighbour sampling; the source resolution is deliberately low. No monitor was flashed. HDMI/DP capture, DDR scanout/scaling and
multi-buffer ownership are outside this model.

## Source and build

The pinned subset under `fw/doom/vendor/Doom8088` is from
https://github.com/FrenkelS/Doom8088 at
`b3073a2eb2811cd14caba6549694fc3bfcd6dd29`. Original copyright notices and GPL
licence are retained. Preparation changes are deterministic in the build
script: remove the things pass, use the optimized fixed maths, place hot
constant tables in CODE and compose wall texture assets offline. The original
BSP and wall-rendering calculations remain C compiled for the 8051.

The recorded build uses awto-sdcc core/MCS51 sources from
`977817123a2cda4df723957574598897c5f4a12d` (4.6.4), plus installed SDAS/SDLD
and ABI-zero large-stack-auto libraries from SDCC 4.5.0 #15242. The cache is
non-reentrant with `--sloc-xdata`; the renderer uses `--stack-auto` and selected
static working records in XRAM. `--xstack` is **not enabled** in this renderer.

The builder handles an important old-assembler compatibility issue. New
compiler output uses inline `bits[0]` expressions. SDAS 4.5 relocates these as
a byte address in an instruction; `SETB bits[0]` then writes the wrong IRAM
byte, potentially a return address. `assemble_c()` emits the canonical
`b0 = bits[0]` alias form used by stock SDCC 4.5. This is done before assembly,
not by changing simulator instructions. The native C integration tests verify
the resulting code and ordinary C call wrappers.

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --wad /path/to/original/doom1.wad --capture-stream
```

Use the original shareware IWAD, not a jWadUtil-preprocessed WAD. It is not
bundled. The recorded input SHA256 was
`1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`.
The asset loader currently supports E1M1's opaque wall textures up to 256x128.
It uses the linked 8051 `sizeof`/`offsetof` schema rather than assuming host
pointer size or structure alignment. Per-object allocations cannot cross a
64 KiB boundary. Asset packing is preparation, not scene rendering.

Outputs in `tmp/doom-renderer/`: Intel HEX/map/memory reports, generated C and
assembly, `renderer-results.json`, native/preview PNGs and a VLC-compatible
MP4 captured from the existing `sim_live` MJPEG handler. That MP4 is a repeated
still, not gameplay or a frame-rate measurement.

## Native optimization and presentation

The original 32-line C cache and byte-at-a-time row-major output took about
780-985 ms per cold frame. The new implementation keeps the original compiled
BSP/projection/clipping calculations, with native assembly for hot memory paths:

- 128 direct-mapped 16-byte cache lines. Separate offset/bank/flag pages let the
  generic pointer bridge test a hit with DPTR1 and access SRAM directly.
- Native cache miss, dirty eviction, retry/poll and full-line write routines.
  Every DDR transfer still executes the MCU_DC register protocol as opcodes.
- Column-major indexed pixels, with a fixed 128-byte column stride. Texture
  columns and colormaps are copied into dedicated SRAM pages before shading. Repeated use of the same immutable texture column now
  skips the 128-byte staging copy entirely.
- Native fixed-point column shading, flat fills and chunk/address traversal.
  The exact wall-step reciprocal uses the existing optimized FixedDiv kernel:
  `floor((0xffffffff/d)/128) = floor((2^25-1)/d)`. It computes
  `floor(2^25/d)` and subtracts one for power-of-two divisors of 2^25.
  Values at/above 2^25 return zero; denominator zero has a defined zero result.
  The low 16 bits match the original C expression across tested uint32 inputs.
- Native 16x16 gather/transpose, planar palette lookup and 48-byte RGB expansion.
  Each tile row is written as three 16-byte bursts. Raster pitch includes the
  full last tile, preventing a partial tile from overwriting the next row.
- Deferred native indexed-buffer clear before every frame. A 256-byte SRAM
  first-touch bitmap replaces writing zeros to DDR then fetching them again.
  First use allocates a zeroed, dirty cache line; later uses reload ordinary
  DDR after eviction. Final flush still materializes the complete cleared
  framebuffer. Clear invalidates old indexed cache tags while preserving
  other banks. Full-line raw writes also mark initialized lines. This preserves
  clipped/unpainted pixels across rotating views.
- Native whole-frame presentation maintains raster/tile addresses in registers
  and the shared scratch overlay, eliminating C long multiplies per output row.
  Palette expansion reads each indexed source byte directly, without the
  former 16-byte IRAM copy.
- Frame-completion hooks stop on the native status write, without polling
  overshoot. A mailbox runs consecutive frames and advances the camera angle.
  Host acknowledgements resume the CPU after capture; Python does not render.

Paged `MOVX @Ri` in these loops uses DW8051's **direct-bus MPAGE at SFR 92h**;
SDCC startup is linked with `__XPAGE` set accordingly. The core's default stays
P2/A0h for existing firmware and tests; only this standalone renderer selects
92h. The Synopsys DW8051 databook describes these two integration choices:
https://www.cs.washington.edu/education/courses/477/02sp/docs/DW8051_databook.pdf
(section 2, external data memory interface). **The scaler's actual MPAGE/P2
wiring has not been verified on hardware.** This is a target configuration
assumption, not evidence of a new scaler feature. The same page loops require
the appropriate SFR selection before a hardware port.

The four immutable trigonometric/projection tables (16,356 bytes) now reside
in bank-zero CODE, using correctly qualified `const __code` arrays/pointers.
The image fits below the absolute schema at F000h. For reproducible packing,
`tables.json` and its DDR copies remain available, but native rendering reads
these four tables using MOVC. Preparation retains the original table values.

The flash model previously charged only opcode fetches, making MOVC data reads
free even on a cold data line. It now charges both MOVC variants' data accesses
through the configured shared flash cache, including PC-relative address
PC-after-opcode + A. New cold/warm tests check exact clocks and cache misses.
All current rates below include this correction. Unified cache geometry is
still an explicit model assumption, not a hardware measurement.

CKCON MOVX stretch is zero, matching the SDK's `_CKCON_MOVX_DEFAULT_CYCLE`
(two instruction cycles). Extra hardware bus waits, IRQs and scaler contention
are not measured by this work.

## Memory and stack

The documented scaler XRAM range is **D700h-F6FFh, 8 KiB**. The simulated
32 MiB DDR is separate, accessed through MCU_DC, and does not enlarge XRAM.

| Storage | Current layout |
|---|---|
| Dynamic C XRAM | D700h-DBD9h: 1,242 bytes at 40x80 / 40x64; 1,152 at 30x64; 1,422 at 60x128 |
| Cache data | E000h-E7FFh: 2,048 bytes |
| Cache offset tags | E800h-E8FFh: 256 bytes |
| Cache bank/valid/dirty tags | E900h-E9FFh: 256 bytes, all nine physical bank bits |
| Planar B/G/R palette | EA00h-ECFFh: 768 bytes |
| RGB burst scratch | ED00h-ED2Fh: 48 bytes |
| Current texture column | ED80h-EDFFh: 128 bytes |
| Current colormap | EE00h-EEFFh: 256 bytes |
| Transpose tile | EF00h-EFFFh: 256 bytes |
| First-touch bitmap | F000h-F0FFh: 256 bytes |
| Status/control/boot | F600h, F630h-F637h, F640h-F681h |
| Hardware stack | SP starts at 20h, 223 bytes available |
| Recorded 64-frame high-water | SP D0h: 176 bytes used, 47 bytes remaining |
| Code/constants | 53,294 occupied bytes at 40x80; 53,423 at 60x128 |
| Indexed DDR | 000F0010h, column stride 128 |
| BGR888 DDR raster | 01F00000h, pitch 144 at 40x80 / 192 at 60x128 |

Fixed SRAM allocations total 4,272 bytes, plus dynamic C storage and mailboxes.
Dynamic XRAM is linked with a 2,304-byte limit so it cannot reach E000h. The
15-byte fixed-maths scratch and native clear/copy/draw/presentation scratch
share the standard 15-byte OSEG overlay. Native gather, palette expansion,
cache fetch/eviction and burst-write callees do not use this overlay. They
must not acquire overlay temporaries while a calling routine has live state.
Interrupts remain disabled, and these routines are mutually exclusive.

Texture/colormap staging identities assume immutable assets and ownership of
their dedicated SRAM pages. A future writer of those assets/pages must first
invalidate the corresponding identity. DdrInit resets both identities.

SDAS expressions use 24-bit values. The builder emits separate byte constants
for 32-bit DDR bases; native presentation initializes the address from those
bytes instead of shifting a truncated/signed assembler value. This matters
for the raster at 01F00000h. Tests reconstruct the full base independently.

The pointer bridge preserves normal XDATA, IDATA, PDATA and CODE tags. Tags
01h..3Fh are a private software ABI for roughly 4 MiB of DDR, not a hardware
MMU. SDCC ignores the tag when testing generic pointer nullness, so low-word
zero is reserved in every 64 KiB bank. Packed objects start after 16 bytes
and never cross a bank boundary. Explicit 32-bit APIs cover all 32 MiB.
E1M1 preloads 473,388 bytes at 30x64: 85 sectors, 475 lines, 732 segs, 236 nodes.

The stack remains internal (`--xstack` is disabled), and the executable runs
without interrupts in register bank zero. The measured margin does not prove
future game logic or arbitrary scenes will fit. Stock `--xstack` uses an 8-bit
pointer and a 256-byte PDATA page; a larger software stack needs compiler and
runtime work. Hardware CALL/RET/interrupt return addresses remain internal.

## 25 FPS result and limits

Recorded with the native executable at 350.791 MHz, SPI CPU/flash ratio 3,
existing flash-fetch/cache model, 32 MiB DDR and **64 extra CPU clocks per DDR
command**. Neither hardware DDR bandwidth nor flash/cache geometry is proven
by this benchmark. No hardware was flashed.

| Viewport | Native frames | Camera step | Runtime frame range | Slowest equivalent FPS |
|---|---:|---:|---:|---:|
| 30x64 | 64 | 11.25 degrees | 21.91-31.27 ms | 31.98 |
| 40x64 | 64 | 11.25 degrees | 26.98-37.94 ms | 26.36 |
| 40x80 | 64 | 11.25 degrees | 29.18-39.86 ms | 25.09 |
| 60x128 | 64 | 11.25 degrees | 46.89-61.94 ms | 16.14 |

At 25 FPS the budget is 40 ms / 14,031,640 CPU clocks. The 40x80 sweep's worst
frame is 39.8588 ms, leaving only 0.1412 ms. Prefer 40x64 when headroom matters:
its worst is 37.9351 ms, leaving 2.0649 ms. Every interval includes logical
indexed clearing, BSP/walls/flat planes, BGR888 conversion, all DDR writes
and final dirty-cache flush. Later intervals include native camera/control
advance. One-time initialization takes 4.7766 ms at 40x80, reported separately
from runtime FPS and included in total `model_ms`. Host capture pauses do not
advance the simulated CPU clock.

This passes a **renderer target for the tested camera position/views**, not
full Doom gameplay or hardware 25 FPS. Actors, sprites, collision, input,
game ticks, sound, IRQs and real scanout remain outside the test. The 40x80
preset has almost no additional CPU budget. 60x128 still fails.

Reproduce the target sweep:

```sh
python scripts/doom_renderer.py --sdcc /path/to/awto-sdcc/bin/sdcc \
  --linker /path/to/sdcc-4.5/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto \
  --wad /path/to/original/doom1.wad --width 40 --height 80 \
  --frames 64 --yaw 0 --yaw-step 11.25 --latency 64 --out tmp/doom-25fps
```

`renderer-results.json` records every native frame interval, render/output
clocks, palette check and DDR counters. `frame-NNN.png` contains the CPU's
actual raster for each view. The delivered 64-frame H.264 rotation plays at
25 FPS for viewing; playback cadence is not the performance measurement.
The older `capture_stream()` / `--capture-stream` check still captures a
repeated still through `sim_live` MJPEG and remains explicitly labelled so.

The independent RGB oracle checks every frame against native indexed DDR.
Consecutive frames at selected angles match independent cold renders exactly;
the original 60x128 start view also remains byte-identical. No invalid DDR
commands, busy-write hazards or PUSH stack wraps occurred in the sweep.

The separate stack microbenchmark adds two 32-bit integers with normal SDCC
`--stack-auto` versus `--stack-auto --xstack`, on the DW instruction core:

| Build | CKCON stretch | CPU clocks | Time at 350.791 MHz |
|---|---:|---:|---:|
| Internal stack | 0 or 1 | 172 | 0.490 us |
| XRAM stack | 0 | 400 | 1.140 us |
| XRAM stack | 1 | 424 | 1.209 us |

Both variants produce the expected sum. These figures include the compiled
callee's frame setup, arithmetic and return, but exclude caller parameter
setup and flash-fetch stalls. They illustrate a small function's overhead,
not a multiplier to apply to Doom's whole runtime. Compiler temporaries can
still use internal RAM even under the tested `--xstack` build.

For native tests set `AWTO_DOOM_SDCC`, `AWTO_DOOM_LINKER`,
`AWTO_DOOM_LIB_LARGE`, `AWTO_DOOM_LIB_STACK`, and optionally `AWTO_DOOM_WAD`:

```sh
python -m pytest -q tests/test_doom_platform.py
```

The four platform cases cover both public C math ABIs, seven DDR banks,
dirty eviction/reload, full-line overwrite coherence, ninth-bank-bit aliases,
normal XDATA/CODE pointers, reserved null offsets, the final byte of 32 MiB
DDR and 1,144 oracle pairs per math function per case. The 90 targeted tests
also cover MPAGE versus P2 selection/reset/snapshot, native code generation,
SRAM pages, partial-tile pitch, both MOVC flash-data reads and rotating-frame
reproducibility. Public C tests additionally check deferred clear, repeated
clear, dirty collision/eviction, raw indexed overwrite, unchanged other banks,
chunk boundary shading/phase wrap, staging-cache hits, and over 4,000 unsigned
reciprocal denominators in each of four ABI/fault cases. All passed,
as did all 297 opcode/stretch timing cases, timers and dual-DPTR checks.
