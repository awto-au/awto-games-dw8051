# Native tagged door switches

Historical format-8 checkpoint. Read [doom-exits.md](doom-exits.md) for the
latest format-9 image, original exit activation and current validation.

24 November 2026. Use-triggered switches can now open one or several door
sectors sharing their tag. The 8051 selects linked targets, changes the original
SW1 wall texture to SW2, moves the doors and restores reusable buttons after
35 controller ticks. This continues the standalone gameplay prototype.
Functionality remains ahead of frame-rate optimisation.

## Play and reproduce

The original E1M1 exit switch is special 11, which remains unsupported. The
supplied demo is an explicit initial test scene: an existing corridor wall
becomes a reusable switch linked to an existing door sector. The original map
geometry is unchanged. Its SW1STRTN/SW2STRTN artwork comes from the shareware IWAD.
All scene changes are applied before CPU boot, never during gameplay.

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad \
  --pose examples/doom-switch-pose.json --scene examples/doom-switch-scene.json
```

Press Space/E while facing the wall switch. It changes texture and opens the
linked door to the right. Wait to see it reset, turn right toward the open door,
then walk through. W/S moves, A/D strafes, arrows turn, Shift moves faster and
F/Ctrl fires. Keys, health/ammo, combat and existing manual doors remain enabled.
At death, stop and rerun the simulator.

The supplied input script reproduces the 59-frame capture:

```sh
python scripts/doom_renderer.py --skip-build --sdcc /path/to/awto-sdcc/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto --out /path/to/current \
  --wad /path/to/doom1.wad --latency 64 \
  --pose examples/doom-switch-pose.json --scene examples/doom-switch-scene.json \
  --commands examples/doom-switch-demo.json
```

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together. The BIN is the complete 128 KiB two-bank image.
See doom-renderer.md for compiler/linker setup when rebuilding. The IWAD,
decoded asset RAM and proprietary SDK are not bundled.

## Supported actions

| Original linedef special | Switch use | Linked door action |
| --- | --- | --- |
| 29 | One shot | Raise, wait, close |
| 63 | Reusable | Raise, wait, close |
| 103 | One shot | Raise and stay |
| 61 | Reusable | Raise and stay |

Mappings were checked against the original
[p_switch.c](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/p_switch.c).
The actual controller remains the preceding standalone door approximation,
not the original Doom sector thinker system.

Each use line resolves its nonzero tag to all matching sector IDs during asset
preparation. The CPU receives a bounded target mask and performs activation.
Zero and unmatched tags cannot broadcast to ordinary tag-zero sectors. Targets
must satisfy the existing door geometry/opening checks; arbitrary rooms,
floors, lifts, crushers, walkover triggers, exits and other specials remain
unsupported. Remote unkeyed switches act on their target sectors independently
of any colour locks on those doors' manual-use lines.

One-shot use is consumed permanently for the session and retains SW2. A reusable
button stays active for 35 controller ticks, then returns to SW1 and can be
pressed again. A fresh press while it is active is ignored. Holding use never
re-triggers it, including after reset; release and press again. Door wait/close
runs independently of the button timer. Wall occlusion, front-side selection,
64-unit use range and conservative door obstruction reopening are preserved.

Where a switch side has a matching SW1/SW2 texture pair, the packer stores that
texture-word address and both original texture IDs. The CPU writes the live
side record, and the ordinary native wall renderer draws the result. A supported
use line without a texture pair can still activate its targets. It receives no
invented replacement graphic. The browser also reports accepted switch uses.

## Data and memory

D805 format 8 enables tagged-switch packing and paired texture preloading.
Older images retain their previous layouts/behaviour. Existing door/actor/
combat/pickup/input/boot record sizes remain unchanged. The door-data header's
previously reserved word pair at offset 8 now contains a uint32 pointer to the
switch table. It is zero for older image formats.

DDR A4010h has a 16-byte header containing a uint16 switch count, then up to
15 fixed 16-byte definitions: uint16 target mask, uint16 source linedef ID,
uint32 live side-texture address, int16 off/on texture IDs and four reserved
bytes. Targets use the existing maximum of 16 native door sectors.

Use tokens retain their manual-door interpretation for low-five-bit IDs 1-16.
IDs 17-31 select switch slots 0-14; bit 5 marks reusable and bit 7 marks
stay-open. Manual colour-lock bits are interpreted only for manual-door IDs.
Even token 255 is checked as the highest reusable stay-open switch, not a lock.

XRAM F750h holds four uint16 values: accepted uses, texture resets, consumed
one-shot bitmask and last accepted switch ID (1-based). F760h has 15 uint8
button timers. The CPU owns all counters, consumption and timer state.

The native bank-zero report is 64,501 code/constant bytes. The existing bank-one
engine remains 5,741 C bytes plus 15 entry bytes. Dynamic XRAM is 2,143 bytes:
2,064 bank zero plus 79 gameplay bank, in addition to fixed caches/mailboxes
and the new fixed switch state. The executable remains two 64 KiB code banks.
Monitor register wiring, contention and scanout remain unverified. No hardware
was flashed, and changes remain uncommitted/unpushed.

## Validation and capture

The final suite passes 184 tests with no skips, including 21 switch tests and
the previous 163 regressions. New coverage includes all four special mappings,
one-shot consumption, reusable reset/rearm, busy-button rejection, held use,
multiple real tagged sectors, empty masks, zero/unmatched tags, front side,
range, wall occlusion, capacity limits, legacy guards and the maximum token/bit.
Independent booting with the original SW2 wall texture confirms the switched
CPU-written pixels; the same crop matches SW1 after native reset.

Every capture frame checks live texture IDs against timer/consumption state,
linked activation counts, world/actor geometry, combat/pickup/key accounting,
RGB conversion, native bank return and DDR errors. Host code prepares assets,
supplies input and captures/verifies output; it does not switch textures,
choose activations, advance doors or render game pixels during play.

The silent model-paced replay contains 59 CPU-written frames. Model frame
durations total 8.91 seconds; MP4 playback adds timing quantization. The switch
activates once, resets once and opens the linked door; the player then walks
through. Worst assumed CPU-model frame is 257.27 ms. Stack high-water is D8h,
leaving 39 of the 223 stack bytes. No stack wraps, invalid DDR commands or
busy-write hazards occurred. These are model timings at the existing assumed
350.791 MHz/64-extra-clock DDR setup, not measured hardware FPS.

The patch retains the previously restored DDR simulator header. A clean exact-
base checkout is patched, rebuilt to the same native image and used to compile
a fresh simulator and verify a real native switch activation.

Next gameplay work includes level exits, larger original maps, more trigger
types, weapons/armor, sound, restart flow and a real-time tick scheduler. The
existing 512-linedef, 128-monster and 128-pickup bounds still apply, together
with 16 doors and 15 switch use lines. Flat plane/sky approximations remain.
