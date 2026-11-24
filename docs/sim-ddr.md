# DDR transport in the fast simulator

`scripts/mcs51_core.c` + `mcs51_ddr.h` implement the MCU DDR port directly in
the fast core. `scripts/ddr_sim.py` resolves register names from the existing
RTD2795T regdb and exposes RAM, counters, faults and a raster capture API.
FastMachine enables it by default; `AWTO_SIM_DDR=off` disables it.

| Behaviour | Basis |
|---|---|
| 32 MiB accessible address space, wraps at 2^22 eight-byte units | Measured on unit 2, 2026-11-20, #267; physical capacity may be greater |
| Two-unit/16-byte commands, write 100, read 101 in CMD[7:5] | Regdb and hardware |
| CMD clears to NOP at completion | Regdb qack description |
| Read buffer halves swapped; write buffer halves swapped | Hardware #255/#267 |
| Mask bit 1 preserves that write-buffer byte's memory lane | Hardware masktest, #267 |
| READ_FLAG cleared by any data-buffer read; data/flag read-only | Regdb |
| LEN 1/4 hangs; unsupported lengths/reserved commands stay busy | LEN 1/4 measured on A; extension to other unsupported values is a conservative model policy |
| A and B share logical backing RAM and lane convention | Model assumption; B mapping not hardware-verified |
| In-flight writes to transaction registers ignored and counted | Model policy to expose driver hazards; not a measured silicon response |
| RAM retained across CPU reset, in-flight command cancelled | Model policy; no DRAM power-cycle model |

Command parameters and write-buffer bytes are latched when the command is
issued. A transaction remains busy until its configured latency has elapsed.
The default adds **zero transport latency**, for functional tests. Set
`AWTO_SIM_DDR_LATENCY_CLK` to add CPU clocks per command. This is **not** a
hardware-calibrated throughput model: the observed 64 us/read includes driver
work and intermittent timeouts. Do not report simulator FPS as measured hardware
FPS. SPI flash fetch and DW8051 instruction timing retain their existing models.

`m.ddr.drop_every(N, port=0)` suppresses every Nth read-ready flag, with CMD still
completing. This deterministic fault exercises a driver's timeout/retry path.
`m.ddr.stats(port)` reports writes, reads, invalid commands, hazards and drops.

`m.ddr.memory` is the host preload/capture view of RAM. Firmware accesses RAM
only through MCU_DC; host memory access does not emulate a firmware command.
`m.ddr.raster(width, height, base=0, pitch=None, line_repeat=1)` returns a PIL RGB
image from BGR888 DDR bytes. Geometry is explicit because the display-address,
capture, multi-buffer and scaling pipeline are not yet emulated. In particular,
HDMI input does not automatically overwrite DDR. This model adds the MCU memory
interface, not a new video pipeline.

Run: `python3 -m pytest -q tests/test_sim_ddr.py`.
The tests execute MOVX opcodes on the DW8051 core and cover both ports, every
mask lane, each accessible unit-address bit, aliasing, busy state, ready flags,
fault recovery, reset, pending-command snapshots and raster colour/stride.
