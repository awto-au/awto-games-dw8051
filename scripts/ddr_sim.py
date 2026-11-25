#!/usr/bin/env python3
"""RTD2795T MCU_DC DDR interface for FastMachine, backed by 32 MiB (one chip).

Transport runs in mcs51_core.c (mcs51_ddr.h), including snapshot/restore.
Addresses: re/regdb/RTD2795T-CG.tsv.gz. Lane order/masks/capacity:
docs/ddr-draw.md, hardware #255/#267. Command latency defaults to ideal (zero
additional clocks), NOT a calibrated hardware speed model. Unsupported burst
lengths/reserved commands stay busy; reset clears the transaction, not RAM.
Hardware: port A = chip A, port B = chip B, 32 MiB each (awto-ddc#348, docs/ddr-map.md).
This model backs both ports with ONE RAM (wrong for B: #5); B lanes unverified.
"""
from __future__ import annotations

from functools import lru_cache

SIZE = 32 * 1024 * 1024
UNIT_BYTES, BURST_BYTES = 8, 16
CMD_WRITE, CMD_READ, READY = 0x80, 0xA0, 1
REG_FIELDS = ("CMD", "LEN", "ADDR_H", "DATABUF_W_00", "DATABUF_R_00", "WMASK_H", "READ_FLAG")


@lru_cache(maxsize=1)
def registers():
    import regdb_query
    rows = regdb_query.load("RTD2795T-CG")
    return {r["register"]: int(r["address"], 0) for r in rows if r["kind"] == "REG" and r["register"].startswith("MCU_DC_")}


def config():
    r = registers()
    return [r[f"MCU_DC_{field}_{port}"] for port in ("A", "B") for field in REG_FIELDS]


class DdrMemory:
    reads = writes = swrites = ()       # native C transport, no per-register Python hooks

    def __init__(self, size=SIZE, latency_clk=0):
        self.size, self.latency_clk = size, latency_clk
        self.core = None

    def init(self, machine):
        self.core = machine.core
        self.core.set_ddr(config(), self.size, self.latency_clk)

    @property
    def memory(self):
        return self.core.ddr_mem()

    def stats(self, port=0):
        return self.core.ddr_stats(port)

    def drop_every(self, n, port=0):
        """Deterministic missing-ready fault: every nth read, 0 disables it."""
        if n < 0 or port not in (0, 1):
            raise ValueError("nonnegative interval, port 0/1 required")
        self.core.L.core_ddr_drop_every(self.core.h, port, n)

    def raster(self, width, height, *, base=0, pitch=None, line_repeat=1):
        """Expose a BGR888 DDR region as a PIL RGB raster, no scaler-output emulation.

        base/pitch are BYTE addresses. Explicit geometry avoids claiming the
        current incomplete M-domain/display register model selects a real scanout.
        """
        import numpy as np
        from PIL import Image
        pitch = width * 3 if pitch is None else pitch
        if min(width, height, line_repeat) <= 0 or base < 0 or pitch < width * 3:
            raise ValueError("invalid DDR raster geometry")
        end = base + (height - 1) * pitch + width * 3
        if end > self.size:
            raise ValueError("DDR raster extends past RAM")
        data = np.ndarray((height, width, 3), dtype=np.uint8, buffer=self.memory, offset=base, strides=(pitch, 3, 1))
        rgb = data[:, :, ::-1].copy()
        if line_repeat != 1:
            rgb = np.repeat(rgb, line_repeat, axis=0)
        return Image.fromarray(rgb)
