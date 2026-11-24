"""Real SDCC C ABI and native DDR pointer/cache tests; optional IWAD render.

Set AWTO_DOOM_SDCC, AWTO_DOOM_LINKER, AWTO_DOOM_LIB_LARGE,
AWTO_DOOM_LIB_STACK to the compiler/driver/runtime directories. No WAD needed
for the platform tests. AWTO_DOOM_WAD enables renderer integration too.
"""
import json
import os
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def toolchain(stack):
    names = ["AWTO_DOOM_SDCC", "AWTO_DOOM_LINKER", "AWTO_DOOM_LIB_STACK" if stack else "AWTO_DOOM_LIB_LARGE"]
    values = [os.environ.get(n) for n in names]
    if not all(values): pytest.skip("set " + ", ".join(names))
    return [Path(v) for v in values]


def build_platform(out, stack, fixture=None, extra_sources=()):
    import doom_renderer as R
    sdcc, linker, libdir = toolchain(stack)
    R.cache_config(out)
    flags = ["-mmcs51", "--model-large", "--std-sdcc11", "--opt-code-speed"]
    asm = ["fixed_math", "ddr_pointer", "fixed_stack_abi" if stack else "fixed_abi", "gptr_cmp", "video", "cache_native"]
    for name in asm:
        R.assemble_runtime(sdcc,out,name)
    fixture=fixture or ROOT/"tests/doom_platform_fw.c"
    for src in [fixture,ROOT/"fw/doom/ddr_cache.c",*extra_sources]:
        extra = ["--stack-auto", "-DDOOM_STACK"] if stack and src.stem != "ddr_cache" else ["--sloc-xdata"]
        R.assemble_c(sdcc,[*flags,*extra],src,out/(src.stem+".rel"))
        rel=out/(src.stem+".rel")
        rel.write_text(rel.read_text().replace(" sdcccall(0)",""))
    objects=[out/(n+".rel") for n in [fixture.stem,"ddr_cache",*(src.stem for src in extra_sources),*asm]]
    R.run([linker,*flags,*( ["--stack-auto"] if stack else []),"--xram-loc","0xD700","--xram-size","0x900",
           "--iram-size","256","--lib-path",libdir,*objects,"-o",out/"platform.ihx"])


@pytest.mark.parametrize("stack",[False,True])
@pytest.mark.parametrize("drop_every",[0,7])
def test_native_c_platform(tmp_path,stack,drop_every):
    import fastmachine as F
    import ddr_sim as D
    import doom_sim as S
    build_platform(tmp_path,stack)
    core=F.Core(S.load_ihx(tmp_path/"platform.ihx"))
    core.set_dw(json.loads(F.MODEL_JSON.read_text()))
    core.reset()
    core.set_xpage_sfr(0x92)
    core.set_ddr(D.config(),latency_clk=64)
    core.L.core_ddr_drop_every(core.h,0,drop_every)
    try:
        for _ in range(1000):
            core.run(100000)
            assert core.p.sp_wrap==0
            if core.xram[0xF600]==0xA5: break
        else: pytest.fail(f"C platform timed out at {core.p.pc:04X}")
        assert core.xram[0xF601]==0
        assert core.ddr_mem()[0x1FFFFFF]==0x51
        assert core.ddr_mem()[0x3FFFFF]==0xD0
        assert core.ddr_stats()["invalid"]==core.ddr_stats()["hazards"]==0
        ram=core.ddr_mem()
        assert bytes(ram[0x16000E:0x160033]) == bytes([0]+[7]*35+[0])
        shaded=[((((0xF123+i*0x1ABC)&0xFFFF)>>9)^0x55)^0xAA for i in range(35)]
        assert bytes(ram[0x16100E:0x161033]) == bytes([0]+shaded+[0])
        if drop_every: assert core.ddr_stats()["dropped"]>0
        # Exercise ordinary compiled C calls, not direct entry to private maths.
        edge=[-0x80000000,-65537,-65536,-1,0,1,255,256,65535,65536,65537,0x7FFFFFFF]
        pairs=[(a,b) for a in edge for b in edge]
        rng=random.Random(8051)
        pairs += [(S.signed(rng.getrandbits(32)),S.signed(rng.getrandbits(32))) for _ in range(1000)]
        for a,b in pairs:
            core.xram[0xF620:0xF628]=(a&0xFFFFFFFF).to_bytes(4,"little")+(b&0xFFFFFFFF).to_bytes(4,"little")
            for op in (1,2):
                core.xram[0xF62C]=op
                core.run(2000)
                assert core.xram[0xF62C]==0
                got=S.signed(int.from_bytes(core.xram[0xF628:0xF62C],"little"))
                assert got==S.reference(a,b,op==2),(a,b,op,got)
        assert core.p.sp_wrap==0
        # Exact unsigned reciprocal over the full uint32 domain, including
        # quotient truncation and every power-of-two correction boundary.
        denominators={1,0x1FFFFFF,0x2000000,0xFFFFFFFF}
        for bit in range(32):
            for delta in (-1,0,1):
                value=(1<<bit)+delta
                if 0<value<=0xFFFFFFFF: denominators.add(value)
        denominators.update(rng.randrange(1,0x100000000) for _ in range(2000))
        denominators.update(rng.randrange(1,0x2000000) for _ in range(2000))
        for d in denominators:
            core.xram[0xF620:0xF624]=d.to_bytes(4,"little")
            core.xram[0xF62C]=3
            core.run(2000)
            assert core.xram[0xF62C]==0
            got=int.from_bytes(core.xram[0xF628:0xF62C],"little")
            assert got==((0xFFFFFFFF//d)>>7)&0xFFFF,(d,got)
    finally: core.free()


@pytest.mark.parametrize("width,height,frames,latency,drop_every",[(60,128,1,64,7),(40,80,8,64,0),(40,64,8,64,0)])
def test_e1m1_renderer(tmp_path,width,height,frames,latency,drop_every):
    import doom_renderer as R
    sdcc,linker,libdir=toolchain(True)
    wad=os.environ.get("AWTO_DOOM_WAD")
    if not wad: pytest.skip("set AWTO_DOOM_WAD to an original Doom 1 shareware IWAD")
    R.build(sdcc,linker,libdir,tmp_path,width=width,height=height)
    result,_=R.simulate(Path(wad),tmp_path,latency=latency,drop_every=drop_every,frames=frames,yaw=0,yaw_step=45)
    assert result["palette_verified"]
    assert result["stack_wraps"]==0
    if drop_every: assert result["ddr"]["dropped"]>0
    if frames > 1:
        # Timing is reported; functional integration has no minimum FPS.
        # Rotating the native renderer must reproduce an independently booted
        # frame: catches stale pixels/cache state across frames.
        from PIL import Image
        for i in (1,4,7):
            R.simulate(Path(wad),tmp_path,yaw=i*45,latency=latency)
            with Image.open(tmp_path/f"frame-{i:03d}.png") as seq, Image.open(tmp_path/"e1m1-native.png") as single:
                assert seq.tobytes()==single.tobytes()
