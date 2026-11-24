# Native normal and secret exit activation

24 November 2026. E1M1's original exit switch now finishes the current level in
the native 8051 prototype. It changes to SW2, latches completion, displays an
8051-drawn EXIT banner and stops gameplay updates. Normal and secret exit uses
are distinguished. The host never substitutes an exit decision or game pixels.

This checkpoint ends at completed-level state. It does not load the next map,
show original intermission statistics or implement episode/campaign routing.
Stop and rerun the simulator to start a fresh session. Functionality remains
ahead of FPS optimisation; this is not the original Doom thinker system.

## Play the original E1M1 exit

The recording uses the original E1M1 exit linedef 330, special 11 and original
SW1STRTN/SW2STRTN artwork. It has no initial scene edits, added switch, changed
tag or replaced geometry. The supplied pose simply starts in its exit room.

```sh
python scripts/doom_play.py --out /path/to/current --wad /path/to/doom1.wad \
  --pose examples/doom-exit-pose.json
```

Walk toward the switch and press Space/E. The native EXIT banner appears and
the browser reports LEVEL COMPLETE. Later move/turn/use/fire commands are
ignored by gameplay. W/S moves, A/D strafes, arrows turn, Shift moves faster
and F/Ctrl fires before completion. Omitting --pose uses the original map spawn.

Replay the recorded inputs with:

```sh
python scripts/doom_renderer.py --skip-build --sdcc /path/to/awto-sdcc/bin/sdcc \
  --libdir /path/to/share/sdcc/lib/large-stack-auto --out /path/to/current \
  --wad /path/to/doom1.wad --latency 64 \
  --pose examples/doom-exit-pose.json --commands examples/doom-exit-demo.json
```

Keep doom_renderer.bin, doom_renderer.ihx, banking.json, tables.json and
cache-config.json together. The BIN is the complete two-bank executable; the
IHX alone is insufficient. See doom-renderer.md for compiler/linker setup.
The IWAD, decoded asset RAM and proprietary SDK are not bundled.

## Rules and completed state

| Original special | Native completion kind | Activation |
| --- | --- | --- |
| 11 | 1, normal exit | Use from the front within the existing 64-unit range |
| 51 | 2, secret exit | Same use/range/visibility rules |

The mappings follow the original
[p_switch.c](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/p_switch.c).
Both exit uses are one-shot and need no tag or door target. Walls can block
use, and the back side cannot activate it. A dead player cannot complete a
level. The native switch changes texture before completion is latched.

An exit shares the existing bounded switch-use table. The table's previously
reserved uint16 at definition offset 12 is now kind: 0 tagged door action,
1 normal exit, 2 secret exit. The fixed definition remains 16 bytes. Exit
lines have an empty door mask; their native kind makes them actionable.
The maximum is 15 combined tagged-switch/exit use lines. An unmodified E1M1
has one exit and no supported tagged-door switches. Older format-8 images
continue to ignore exit specials rather than treating them as door actions.

XRAM F770h contains four uint16 values: completion kind, source linedef ID,
accepted-exit count and a reserved word. Initial kind/count/reserved are zero;
the initial source is FFFFh. A completed session has exactly one accepted exit.
D805 marker version 9 enables this layout and original exit packing. Other
boot/input/door/actor/combat/key/pickup/fireball record sizes are unchanged.

The exit tick may already have applied its input turn and incremented the
controller tick count before tracing use. Once it accepts the exit, translation,
additional controller ticks and subsequent actor/combat/pickup/projectile updates
stop. Existing door/button/key timers also stop. Native rendering continues to
show the last world state with the EXIT banner. Even render-only host yaw steps
cannot rotate a completed scene. Input mailboxes and rendering/frame counters
can still change; they do not advance gameplay.

Both the completed state and banner are native. Banner glyphs use a small
8051-drawn bitmap font; no host image overlay supplies the game message. The
browser only displays the reported state. The input path continues to send
commands, so freeze checks exercise the CPU's rejection of later input.

## Verification and memory

The final suite has 199 passing tests with no skips: the preceding 184 plus
15 exit checks. Coverage includes normal/secret kinds, an exit-only world with
no door sectors, one-shot state, range/front side/wall rejection, original
E1M1 loading, format-8 compatibility, dead players, frozen input, a fireball
already in flight, render-only yaw and the maximum combined switch/exit slot.
An independent glyph oracle verifies every EXIT letter pixel in the native
framebuffer. Existing combat, key, pickup, tagged-switch, geometry, bank,
maths, DDR, HUD and HTTP/MJPEG regressions remain passing.

Every captured frame checks completion against its original packed exit line,
exactly-once state and positive player health. After completion it verifies
unchanged gameplay records for motion, actors, projectiles, combat, pickups,
keys, switches and doors. Normal world/profile, resource-accounting, palette,
bank-return and DDR checks remain enabled. The recorded completed frames are
pixel-identical despite later movement, turning, use and fire input.

Bank-zero code/constants report 64,985 bytes. Bank-one gameplay remains
5,741 C bytes plus 15 entry bytes. Dynamic XRAM remains 2,143 bytes (2,064
bank zero and 79 gameplay bank), plus existing fixed state and the new eight
completion bytes. The complete executable remains two 64 KiB native code banks.
Actual monitor memory wiring, contention and scanout remain unverified. No
hardware was flashed and changes remain uncommitted/unpushed.

## Capture and restoration

The 41-frame original exit-room recording walks toward the existing switch,
activates it on frame 20 and then supplies move/turn/use/fire commands for
20 more frames. The level remains completed with normal kind, source line 330
and one exit activation. The native banner remains visible; health/ammo stay
100/50. This is an original exit-room demonstration, not a claimed full-level
playthrough from spawn.

The silent movie approximately follows recorded CPU-model durations. Worst
model frame is 101.54 ms in this particular view; it is not measured hardware
FPS or an optimisation claim. The existing model assumes 350.791 MHz and 64
extra clocks per DDR command. Native gameplay still uses the existing fixed
35/25 controller-tick budget per rendered frame before completion.

Capture stack high-water is D6h, leaving 41 of 223 stack bytes. There were no
stack wraps, invalid DDR commands or busy-write hazards. Clean exact-base
patch restoration, an identical native rebuild and a freshly compiled
simulator are checked with an actual normal-exit activation. The previously
restored DDR simulator header remains in the patch.

Next work includes intermission/next-map flow, larger maps, weapon/armor
inventory, more trigger types, sound, restart flow and a real-time tick
scheduler. The 512-linedef map bound still excludes original E1M2/E1M3, so
this update does not claim a playable campaign or a complete Doom port.
