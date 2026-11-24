#!/usr/bin/env python3
"""Execute Doom fixed maths and the existing DDR firmware on the DDC DW8051 core.

python scripts/doom_sim.py --sdcc /path/to/sdcc --libdir /path/to/lib/large-stack-auto
Optional --serve PORT reuses sim_live's VLC MJPEG endpoint for the captured raster.
This is an arithmetic/DDR harness, NOT a completed Doom game port.
"""
from __future__ import annotations
import argparse
import io
import json
import random
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import fastmachine as F
import ddr_sim as D

CPU_HZ = 350_791_000
STATUS = 0xF600
RETURN_PC = 0xFF00


def load_ihx(path):
    image = bytearray(65536)
    for line in Path(path).read_text().splitlines():
        b = bytes.fromhex(line[1:])
        if sum(b) & 255:
            raise ValueError("bad Intel HEX checksum")
        n, addr, typ = b[0], int.from_bytes(b[1:3], "big"), b[3]
        if typ == 0:
            if addr + n > len(image):
                raise ValueError("image outside code bank")
            image[addr:addr+n] = b[4:4+n]
        elif typ == 1:
            break
        else:
            raise ValueError(f"unsupported Intel HEX record {typ}")
    return bytes(image)


def command(argv):
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=60)
    if p.returncode:
        raise RuntimeError(f"{argv}:\n{p.stdout}\n{p.stderr}")
    return p


def build(sdcc, libdir, out):
    bindir = sdcc.parent
    command([bindir / "sdas8051", "-losg", out / "fixed_math.rel", ROOT / "fw/doom/fixed_math.asm"])
    command([bindir / "sdld", "-n", "-i", "-m", "-w", "-b", "CSEG=0x0100", "-b", "DSEG=0x30", out / "fixed_math", out / "fixed_math.rel"])
    command([sdcc, "-mmcs51", "--model-large", "--stack-auto", "--opt-code-speed", "--xram-loc", "0xD700", "--xram-size", "0x1E00",
             "--iram-size", "256", "--lib-path", libdir, ROOT / "tests/ddr_sim_fw.c", "-o", out / "ddr_sim_fw.ihx"])


def signed(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def reference(a, b, divide):
    if not divide:
        return signed((a * b) >> 16)
    if abs(a) >> 14 >= abs(b):
        return -0x80000000 if (a < 0) != (b < 0) else 0x7FFFFFFF
    q = (abs(a) << 16) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def math_check(out, count=10000):
    image = load_ihx(out / "fixed_math.ihx")
    text = (out / "fixed_math.map").read_text()
    symbols = {name: int(addr, 16) for addr, name in re.findall(r"(?:C:)?\s*([0-9A-Fa-f]{8})\s+(_DoomFixed\w+)", text)}
    c = F.Core(image)
    model = json.loads(F.MODEL_JSON.read_text())
    c.set_dw(model)
    c.set_fetch(model)
    c.xram[0xFDA0] = 1                 # same flash-cache enable register as firmware
    c.L.core_set_fetch_ratio(c.h, 3 * 256)  # 350.8 / 116.9 MHz
    c.set_ddr(D.config())              # same machine configuration as renderer
    c.pch[RETURN_PC] = 1
    edge = [-0x80000000, -0x7FFFFFFF, -65537, -65536, -65535, -1, 0, 1, 2, 255, 256, 65535, 65536, 65537, 0x7FFFFFFF]
    pairs = [(a, b) for a in edge for b in edge]
    rng = random.Random(0xD00518051)
    pairs += [(signed(rng.getrandbits(32)), signed(rng.getrandbits(32))) for _ in range(count)]
    pairs += [(rng.randrange(-1 << 27, 1 << 27), rng.randrange(-1 << 23, 1 << 23)) for _ in range(count // 4)]
    # Exercise the specialised denominator and integral-operand paths, not just
    # uniform 32-bit inputs (which almost never hit them).
    for _ in range(count // 4):
        small = rng.randrange(1, 256)
        medium = rng.randrange(256, 65536)
        pairs.append((rng.randrange(-(small << 14) + 1, small << 14), small * rng.choice((-1, 1))))
        pairs.append((rng.randrange(-(medium << 14) + 1, medium << 14), medium * rng.choice((-1, 1))))
        pairs.append((rng.randrange(-32768, 32768) << 16, signed(rng.getrandbits(32))))
        pairs.append((signed(rng.getrandbits(32)), rng.randrange(-32768, 32768) << 16))
    for denominator in (1, 2, 255, 256, 65535, 65536, 131071):
        for delta in (-1, 0, 1):
            n = (denominator << 14) + delta
            if n <= 0x7FFFFFFF:
                pairs += [(n, denominator), (-n, denominator), (n, -denominator), (-n, -denominator)]
    result = {}
    try:
        for name, div in (("_DoomFixedMul", False), ("_DoomFixedDiv", True)):
            clocks = []
            classes = {}
            for i, (a, b) in enumerate(pairs):
                bank = (i % 4) * 8
                c.iram[bank:bank+4] = (b & 0xFFFFFFFF).to_bytes(4, "big")
                c.iram[bank+4:bank+8] = (a & 0xFFFFFFFF).to_bytes(4, "big")
                c.sfr[0x50] = bank | (0x80 if i & 1 else 0)  # exercise every register bank and incoming carry
                c.sfr[0x01] = 0x81
                c.iram[0x80:0x82] = RETURN_PC.to_bytes(2, "little")
                c.p.pc = symbols[name]
                c.p.skip_pc = 0xFFFFFFFF
                t0 = c.p.clk
                if c.run(10000) != F.R_PC or c.p.pc != RETURN_PC:
                    raise AssertionError(f"{name} failed to return")
                got = signed(int.from_bytes(c.iram[bank+4:bank+8], "big"))
                want = reference(a, b, div)
                if got != want:
                    raise AssertionError(f"{name}({a},{b}): {got}, expected {want}")
                clocks.append(c.p.clk - t0)
                kind = ("saturated" if (abs(a) >> 14) >= abs(b) else f"div{8 if abs(b) < 256 else 16 if abs(b) < 65536 else 32}") if div else (
                    "integral" if (a & 65535) == 0 or (b & 65535) == 0 else "fractional")
                classes.setdefault(kind, []).append(clocks[-1])
            result[name] = dict(vectors=len(pairs), failures=0, min_clk=min(clocks), median_clk=statistics.median(clocks), max_clk=max(clocks),
                                median_us=statistics.median(clocks) * 1e6 / CPU_HZ,
                                paths={k: dict(n=len(v), median_clk=statistics.median(v), median_us=statistics.median(v)*1e6/CPU_HZ) for k,v in classes.items()})
            print(name, result[name], flush=True)
    finally:
        c.free()
    return result


def firmware_check(out, drop_every=0):
    c = F.Core(load_ihx(out / "ddr_sim_fw.ihx"))
    c.set_dw(json.loads(F.MODEL_JSON.read_text()))
    c.reset()
    c.set_ddr(D.config())
    c.L.core_ddr_drop_every(c.h, 0, drop_every)
    t0 = time.monotonic()
    try:
        for _ in range(1000):
            r = c.run(100000)
            if r not in (F.R_DONE, F.R_PC):
                raise AssertionError(f"firmware stopped: {r}, pc={c.p.pc:x}")
            if c.xram[STATUS] == 0xA5:
                break
        else:
            raise AssertionError("DDR firmware did not finish within 100M instructions")
        status = list(c.xram[STATUS:STATUS+7])
        assert status[:6] == [0xA5, 2, 2, 2, 0, 1], status
        assert bool(status[6]) == bool(drop_every), status
        ddr = D.DdrMemory()
        ddr.core = c
        im = ddr.raster(128, 64, pitch=3840 * 3, line_repeat=2)
        filename = out / ("ddr-retry.png" if drop_every else "ddr-figure.png")
        im.save(filename)
        result = dict(status=status, instructions=c.p.instr, cpu_clk=c.p.clk, stack_high=c.p.sp_max, stack_wraps=c.p.sp_wrap,
                      ddr=ddr.stats(), host_seconds=round(time.monotonic()-t0, 3), capture=filename.name)
        assert result["ddr"]["hazards"] == 0 and not result["stack_wraps"], result
        print("DDR firmware", result, flush=True)
        return result, im
    finally:
        c.free()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sdcc", type=Path, default=shutil.which("sdcc"))
    ap.add_argument("--libdir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "tmp/doom-sim")
    ap.add_argument("--math-vectors", type=int, default=10000)
    ap.add_argument("--serve", type=int)
    ap.add_argument("--capture-stream", action="store_true", help="validate the VLC endpoint and record one second to MP4, then stop")
    a = ap.parse_args()
    if a.sdcc is None:
        ap.error("pass --sdcc /path/to/sdcc")
    a.sdcc, a.out = Path(a.sdcc).resolve(), a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    build(a.sdcc, a.libdir.resolve(), a.out)
    result = dict(cpu_hz=CPU_HZ, math=math_check(a.out, a.math_vectors))
    result["ddr_clean"], image = firmware_check(a.out)
    result["ddr_retry"], _ = firmware_check(a.out, 7)
    result["scope"] = "Native 8051 math + actual DDR draw/verify firmware; not a full Doom engine. Transport latency ideal; not hardware FPS."
    (a.out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    if a.serve or a.capture_stream:
        from http.server import ThreadingHTTPServer
        from sim_live import Stream, LATEST
        import threading
        import urllib.request
        buf = io.BytesIO()
        image.save(buf, "JPEG", quality=95)
        LATEST["jpg"] = buf.getvalue()
        server = ThreadingHTTPServer(("127.0.0.1", a.serve or 0), Stream)
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"VLC: {url}/stream", flush=True)
        if a.capture_stream:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with urllib.request.urlopen(url + "/frame.jpg", timeout=5) as response:
                    jpeg = response.read()
                assert jpeg.startswith(b"\xff\xd8")
                (a.out / "vlc-frame.jpg").write_bytes(jpeg)
                command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "mpjpeg", "-r", "4", "-i", url + "/stream",
                         "-t", "1", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", a.out / "vlc-capture.mp4"])
                result["vlc"] = dict(jpeg_bytes=len(jpeg), video="vlc-capture.mp4", validated=True)
                (a.out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
                print("VLC endpoint and MP4 capture passed", flush=True)
            finally:
                server.shutdown()
                server.server_close()
        else:
            server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
