"""Real MOVX instructions on the DDC DW8051 fast core, not a host-only DDR mock."""
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ddr_sim as D
import fastmachine as F

R = D.registers()


class Bus:
    def __init__(self, latency=0):
        self.c = F.Core(bytes(65536))
        self.c.set_dw(json.loads(F.MODEL_JSON.read_text()))
        self.c.reset()
        self.c.set_ddr(D.config(), latency_clk=latency)
        self.code = bytearray()

    def wr(self, reg, value):
        self.code += bytes((0x90, reg >> 8, reg & 255, 0x74, value & 255, 0xF0))

    def rd(self, reg, out=0x40):
        self.code += bytes((0x90, reg >> 8, reg & 255, 0xE0, 0xF5, out))

    def run(self):
        n = len(self.code)
        assert n < 65536
        self.c.code[:n] = self.code
        self.c.p.pc = 0
        self.c.p.skip_pc = 0xFFFFFFFF
        self.c.pch[n] = 1
        assert self.c.run(100_000) == F.R_PC
        self.c.pch[n] = 0
        self.code.clear()

    def addr(self, unit, port="A"):
        start = R[f"MCU_DC_ADDR_H_{port}"]
        for j, v in enumerate(unit.to_bytes(4, "big")):
            self.wr(start + j, v)

    def write(self, unit, data, mask=0, port="A"):
        self.addr(unit, port)
        for j, v in enumerate(data):
            self.wr(R[f"MCU_DC_DATABUF_W_00_{port}"] + j, v)
        self.wr(R[f"MCU_DC_WMASK_H_{port}"], mask >> 8)
        self.wr(R[f"MCU_DC_WMASK_L_{port}"], mask)
        self.wr(R[f"MCU_DC_CMD_{port}"], D.CMD_WRITE)

    def read(self, unit, port="A"):
        self.addr(unit, port)
        self.wr(R[f"MCU_DC_CMD_{port}"], D.CMD_READ)
        self.rd(R[f"MCU_DC_READ_FLAG_{port}"], 0x50)
        for j in range(16):
            self.rd(R[f"MCU_DC_DATABUF_R_00_{port}"] + j, 0x60 + j)
        self.rd(R[f"MCU_DC_READ_FLAG_{port}"], 0x51)


@pytest.fixture
def bus():
    b = Bus()
    yield b
    b.c.free()


@pytest.mark.parametrize("port", ("A", "B"))
def test_roundtrip_and_read_flag(bus, port):
    data = bytes(range(16))
    bus.write(258, data, port=port)
    bus.read(258, port)
    bus.run()
    assert bytes(bus.c.ddr_mem()[258 * 8:258 * 8 + 16]) == data[8:] + data[:8]
    assert bytes(bus.c.iram[0x60:0x70]) == data
    assert (bus.c.iram[0x50], bus.c.iram[0x51]) == (1, 0)
    assert bus.c.ddr_stats(port == "B") == dict(writes=1, reads=1, invalid=0, hazards=0, dropped=0)


def test_flag_clears_on_first_data_byte_and_is_read_only(bus):
    bus.wr(R["MCU_DC_CMD_A"], D.CMD_READ)
    bus.rd(R["MCU_DC_READ_FLAG_A"], 0x50)
    bus.rd(R["MCU_DC_DATABUF_R_00_A"] + 7)
    bus.rd(R["MCU_DC_READ_FLAG_A"], 0x51)
    bus.wr(R["MCU_DC_READ_FLAG_A"], 1)
    bus.rd(R["MCU_DC_READ_FLAG_A"], 0x52)
    bus.run()
    assert list(bus.c.iram[0x50:0x53]) == [1, 0, 0]


def test_every_mask_lane_preserves_the_other_bytes(bus):
    first, second = bytes(range(16)), bytes(range(0x80, 0x90))
    for lane in range(16):
        unit = lane * 2
        bus.write(unit, first)
        bus.write(unit, second, mask=0xFFFF ^ (1 << lane))
        bus.read(unit)
        bus.run()
        want = bytearray(first)
        want[lane] = second[lane]
        assert bytes(bus.c.iram[0x60:0x70]) == bytes(want)


def test_all_address_bits_and_32_mib_alias(bus):
    rng = random.Random(0x2795)
    units = [0, (D.SIZE // 8) - 2] + [1 << n for n in range(1, 22)]
    expected = {}
    for unit in units:
        data = rng.randbytes(16)
        expected[unit] = data
        bus.write(unit, data)
        bus.run()
    for unit, want in expected.items():
        bus.read(unit)
        bus.run()
        assert bytes(bus.c.iram[0x60:0x70]) == want, hex(unit)
    marker = bytes(range(0xE0, 0xF0))
    bus.write(D.SIZE // 8, marker)
    bus.read(0)
    bus.run()
    assert bytes(bus.c.iram[0x60:0x70]) == marker
    assert len(bus.c.ddr_mem()) == D.SIZE


def test_ports_share_backing_memory(bus):
    marker = bytes(range(16))
    bus.write(512, marker, port="A")
    bus.read(512, port="B")
    bus.run()
    assert bytes(bus.c.iram[0x60:0x70]) == marker


def test_busy_and_latched_transaction():
    b = Bus(latency=1000)
    try:
        b.write(0, bytes(range(16)))
        b.rd(R["MCU_DC_CMD_A"], 0x50)
        b.wr(R["MCU_DC_DATABUF_W_00_A"], 255)  # illegal while in flight
        b.wr(R["MCU_DC_CMD_A"], D.CMD_READ)     # cannot replace pending write
        b.run()
        assert b.c.iram[0x50] == D.CMD_WRITE
        assert b.c.ddr_stats()["hazards"] == 2
        b.c.code[:2] = b"\x80\xfe"
        b.c.p.pc = 0
        b.c.run(1000)
        assert b.c.xram[R["MCU_DC_CMD_A"]] == 0
        assert bytes(b.c.ddr_mem()[:16]) == bytes(range(8, 16)) + bytes(range(8))
    finally:
        b.c.free()


@pytest.mark.parametrize("length,command", ((1, D.CMD_READ), (4, D.CMD_WRITE), (2, 0x20)))
def test_unsupported_transaction_stays_busy_until_reset(bus, length, command):
    bus.c.ddr_mem()[123] = 77
    bus.wr(R["MCU_DC_LEN_A"], length)
    bus.wr(R["MCU_DC_CMD_A"], command)
    bus.rd(R["MCU_DC_CMD_A"], 0x50)
    bus.run()
    assert bus.c.iram[0x50] == command
    assert bus.c.ddr_stats()["invalid"] == 1
    bus.c.reset()
    assert bus.c.xram[R["MCU_DC_CMD_A"]] == 0
    assert bus.c.xram[R["MCU_DC_LEN_A"]] == 2
    assert bus.c.ddr_mem()[123] == 77


def test_missing_ready_fault_recovers_on_next_transaction(bus):
    bus.c.L.core_ddr_drop_every(bus.c.h, 0, 2)
    for want in (1, 0, 1):
        bus.wr(R["MCU_DC_CMD_A"], D.CMD_READ)
        bus.rd(R["MCU_DC_READ_FLAG_A"], 0x50)
        bus.run()
        assert bus.c.iram[0x50] == want
        assert bus.c.xram[R["MCU_DC_CMD_A"]] == 0
    assert bus.c.ddr_stats()["dropped"] == 1


def test_snapshot_restores_ddr_pending_transfer_and_counters():
    b = Bus(latency=1000)
    try:
        b.write(0, bytes(range(16)))
        b.run()
        snap = b.c.snap()
        b.c.code[:2] = b"\x80\xfe"
        for _ in range(2):
            b.c.restore(snap)
            assert bytes(b.c.ddr_mem()[:16]) == bytes(16)
            assert b.c.ddr_stats()["writes"] == 0
            b.c.p.pc = 0
            b.c.run(1000)
            assert bytes(b.c.ddr_mem()[:16]) == bytes(range(8, 16)) + bytes(range(8))
            assert b.c.ddr_stats()["writes"] == 1
    finally:
        b.c.free()


def test_raster_pitch_colour_order_and_bounds(bus):
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    d = D.DdrMemory()
    d.core = bus.c
    bus.c.ddr_mem()[16:32] = bytes((0, 0, 255, 0, 255, 0, 9, 9, 255, 0, 0, 255, 255, 255, 9, 9))
    im = d.raster(2, 2, base=16, pitch=8, line_repeat=2)
    assert im.size == (2, 4)
    assert list(im.get_flattened_data()) == [(255, 0, 0), (0, 255, 0)] * 2 + [(0, 0, 255), (255, 255, 255)] * 2
    with pytest.raises(ValueError):
        d.raster(2, 2, base=D.SIZE - 1)


@pytest.mark.parametrize("custom", (False, True))
def test_fastmachine_attaches_ddr_and_snapshots_it(tmp_path, monkeypatch, custom):
    monkeypatch.setenv("AWTO_SIM_DDR", "on")
    monkeypatch.setenv("AWTO_SIM_FETCH", "off")
    mp = tmp_path / "image.map"
    mp.write_text("")
    devices = [D.DdrMemory(size=1024 * 1024)] if custom else []
    m = F.FastMachine(bytes(65536), mp, "ddr-attach-test", devs=devices, ret_pc=0)
    try:
        assert len(m.ddr.memory) == (1024 * 1024 if custom else D.SIZE)
        assert sum(isinstance(d, D.DdrMemory) for d in m.devs) == 1
        m.ddr.memory[-1] = 42
        snap = m.snapshot()
        m.ddr.memory[-1] = 77
        m.restore(snap)
        assert m.ddr.memory[-1] == 42
        assert m.ddr.core is m.core
    finally:
        m.core.free()
