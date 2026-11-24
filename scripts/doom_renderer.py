#!/usr/bin/env python3
"""Build/run the first native Doom8088 wall/BSP renderer on the DDC fast core.

No host rendering: Python packs WAD assets and loads simulated DDR, then the
8051 executes projection, BSP traversal, clipping, columns and palette output.
This is renderer/controller bring-up with native combat, fireballs and pickups, not a complete Doom port.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fw/doom/vendor/Doom8088"
FLAGS = ["-mmcs51", "--model-large", "--stack-auto", "--opt-code-speed",
         "--std-sdcc11", "--disable-warning", "283", "-DC_ONLY", "-DFLAT_SPAN",
         "-DFLAT_SKY", "-DPROFILING"]


def run(args, **kw):
    kw.setdefault("timeout",120)
    p = subprocess.run([str(a) for a in args], stdin=subprocess.DEVNULL, capture_output=True, text=True, **kw)
    if p.returncode:
        raise RuntimeError(" ".join(map(str, args)) + "\n" + p.stdout + p.stderr)
    return p.stdout


def function_replace(text, name, replacement):
    # Applied to preprocessed C, with no braces in strings in these functions.
    m = re.search(r"^[^;{}\n]*\b" + name + r"\s*\([^;{}]*?\)\s*\{", text, re.M)
    if not m:
        raise ValueError("function not found: " + name)
    pos, depth = m.end(), 1
    while depth:
        if text[pos] == "{": depth += 1
        elif text[pos] == "}": depth -= 1
        pos += 1
    return text[:m.start()] + replacement + text[pos:]


def assemble_c(sdcc, flags, src, output):
    """Keep new compiler output compatible with installed SDAS 4.5.

    SDAS 4.5 correctly relocates a bit alias (b0 = bits[0]), but interprets
    inline relocatable bits[0] in an instruction as the byte address. That
    writes another IRAM byte, potentially a return address. Emit the canonical
    alias form used by stock SDCC 4.5; never paper over this at runtime.
    """
    asm = output.with_suffix(".asm")
    run([sdcc,*flags,"-S",src,"-o",asm])
    text = asm.read_text()
    if "bits[" in text and not re.search(r"^\s*b0\s*=",text,re.M):
        text = re.sub(r"bits\[([0-7])\]",r"doom_b\1",text)
        aliases = "\n".join(f"doom_b{i} = bits[{i}]" for i in range(8))
        text = re.sub(r"(\nbits:\n\s*\.ds 1\n)",r"\1"+aliases+"\n",text)
    text = text.replace(" sdcccall(0)","")
    if src.name == "ddr_cache.c":
        # Cache misses never call Doom fixed maths, and fixed maths never
        # accesses DDR. With interrupts disabled their DATA scratch can share
        # one bounded overlay; pointer-bridge return scratch remains separate.
        text = text.replace(".area DSEG    (DATA)",".area OSEG (OVR,DATA)")
    asm.write_text(text)
    run([sdcc.parent/"sdas8051","-losg",output,asm])


def cache_config(out, overrides=None):
    import ddr_sim
    if overrides is None and (out/"cache-config.json").exists():
        return json.loads((out/"cache-config.json").read_text())
    header = (ROOT/"fw/doom/cache_config.h").read_text()
    values = {name:int(value,0) for name,value in re.findall(r"^#define\s+(DOOM_\w+)\s+(0x[0-9A-Fa-f]+|\d+)\s*$",header,re.M)}
    regs = ddr_sim.registers()
    for name,reg in {"WRITE_BASE":"DATABUF_W_00", "READ_BASE":"DATABUF_R_00", "CMD":"CMD", "LEN":"LEN",
                     "ADDR_H":"ADDR_H", "READ_FLAG":"READ_FLAG", "MASK_H":"WMASK_H"}.items():
        values["DOOM_MCU_DC_"+name] = regs["MCU_DC_"+reg+"_A"]
    sdk_rel = "fw/sdk/Project/Header/AwtoRegs.h"   # SDK header stays in awto-ddc ($AWTO_DDC_REPO), not vendored here
    sdk_path = next((p for p in (ROOT/sdk_rel, Path(os.environ.get("AWTO_DDC_REPO", "/mnt/2tb/git/awto-ddc"))/sdk_rel) if p.exists()), ROOT/sdk_rel)
    sdk = sdk_path.read_text()
    values["DOOM_MCU_DC_CMD_MASK"] = int(re.search(r"#define\s+AWTO_F_MCU_DC_CMD_A_DDR_A_CMD\s+(0x[0-9A-Fa-f]+)",sdk).group(1),0)
    values.update(overrides or {})
    # Presentation writes complete 16-pixel tiles, including right-edge padding.
    values["DOOM_RASTER_PITCH"] = ((values["DOOM_VIEW_WIDTH"]+15)//16)*48
    # SDAS stores expression values in 24 bits; a 32-bit DDR base must not be
    # right-shifted there. Emit its four bytes from Python's full-width value.
    for name in ("DOOM_INDEXED_BASE", "DOOM_RASTER_BASE"):
        for byte in range(4): values[f"{name}_BYTE{byte}"] = (values[name] >> (byte*8)) & 255
    values["DOOM_FRAME_INDEXED_BYTES"] = ((values["DOOM_VIEW_WIDTH"]+15)//16)*16*values["DOOM_TEXTURE_COLUMN_SIZE"]
    assert values["DOOM_CACHE_LINES"] == 128
    (out/"doom_cache_config.inc").write_text("\n".join(f"{name} = 0x{value:X}" for name,value in values.items())+"\n")
    (out/"cache-config.json").write_text(json.dumps(values,indent=2)+"\n")
    return values


def assemble_runtime(sdcc, out, name):
    source = ROOT/"fw/doom"/(name+".asm")
    if name == "fixed_math":
        target = out/"fixed_math.asm"
        target.write_text(source.read_text().replace(".area DSEG (DATA)",".area OSEG (OVR,DATA)"))
        source = target
    run([sdcc.parent/"sdas8051","-losg","-I"+str(out),out/(name+".rel"),source])


def prepare(sdcc, out, flags, width, height):
    import shutil
    for p in SOURCE.glob("*.h"): shutil.copyfile(p, out / p.name)
    (out / "compiler.h").write_text("""#ifndef __COMPILER__
#define __COMPILER__
#define __far
#define LITTLE_ENDIAN 1234
#define BIG_ENDIAN 4321
#define BYTE_ORDER LITTLE_ENDIAN
typedef uint16_t segment_t;
#define SIZE_OF_SEGMENT_T 2
#define D_MK_FP(s,o) ((void*)(s))
#define D_FP_SEG(p) ((segment_t)(p))
#define D_FP_OFF(p) 0
#define _fmemcmp memcmp
#define _fmemcpy memcpy
#define _fmemset memset
#define _fstrcpy strcpy
#define _fstrlen strlen
#endif
""")
    p = out / "config.h"
    p.write_text(p.read_text().replace("__attribute__((packed))", "").replace("#define inline __inline__", "#define inline inline"))
    p = out / "r_main.h"
    p.write_text(p.read_text().replace("fullcolormap[256 * 34]", "*fullcolormap"))
    p = out/"doomdef.h"
    p.write_text(re.sub(r"(#define\s+VIEWWINDOWHEIGHT\s+)128\b",rf"\g<1>{height}",p.read_text()))
    for f in ("r_draw.c", "tables.c"): shutil.copyfile(SOURCE / f, out / f)
    text = run([sdcc, *flags, "-E", out / "r_draw.c"])
    text = re.sub(r"^#line.*\n", "", text, flags=re.M)
    text = re.sub(r"^inline\s*\n", "", text, flags=re.M)
    # Remove the thing/sprite pass for this explicitly renderer-only milestone.
    start = text.index("typedef struct vissprite_s")
    end = text.index("static fixed_t R_ScaleFromGlobalAngle", start)
    text = text[:start] + text[end:]
    start = text.index("static void R_ProjectSprite")
    end = text.index("static void R_RenderSegLoop", start)
    text = text[:start] + """
void R_PlatformTexture(int16_t n, int16_t col, draw_column_vars_t *dc);
static void R_DrawSegTextureColumn(const texture_t *tex, int16_t n, int16_t col, draw_column_vars_t *dc)
{ tex; R_PlatformTexture(n, col, dc); }
""" + text[end:]
    for name in ("R_DrawMaskedColumn", "R_InitColormaps"):
        text = function_replace(text, name, "")
    text = re.sub(r"^.*R_AddSprites\(sub, frontsector->lightlevel\);.*$", "", text, flags=re.M)
    text = text.replace("R_ClearSprites ();", "").replace("R_DrawMasked ();", "")
    text = function_replace(text, "FixedMul", "")
    text = function_replace(text, "FixedMul3232", "")
    text = function_replace(text, "FixedMulAngle", "fixed_t FixedMulAngle(fixed_t a, fixed_t b) { return FixedMul(a,b); }")
    text = function_replace(text, "FixedMul3216", "fixed_t FixedMul3216(fixed_t a, uint16_t b) { return FixedMul(a,(fixed_t)b); }")
    text = function_replace(text, "FixedApproxDiv", "fixed_t FixedDiv(fixed_t a, fixed_t b);\nfixed_t FixedApproxDiv(fixed_t a, fixed_t b) { return FixedDiv(a,b); }")
    text = text.replace("(0xffffffffu/((uint32_t)rw_scale)) >> (8 - 1)",
                        "DoomReciprocalStep((uint32_t)rw_scale)")
    # awto-sdcc currently drops the generic tag in this pointer/null ternary.
    # Preserve a real generic pointer assignment in an explicit branch.
    text = text.replace("backsector = line->backsectornum != (0xff) ? &_g_sectors[line->backsectornum] : ((void *)0);",
                        "backsector = 0; if (line->backsectornum != 255) backsector = &_g_sectors[line->backsectornum];")
    # The renderer is single-threaded and non-recursive (PROFILING BSP walk).
    # Keep its large local working records in XRAM rather than the 223-byte
    # hardware stack. Parameters and compiler temporaries still use the stack.
    for func in ("R_RenderSegLoop", "R_StoreWallRange", "R_Subsector", "R_RenderBSPNode", "R_PointToDist"):
        m = re.search(r"^[^;{}\n]*\b" + func + r"\s*\([^;{}]*?\)\s*\{", text, re.M)
        pos, depth = m.end(), 1
        while depth:
            if text[pos] == "{": depth += 1
            elif text[pos] == "}": depth -= 1
            pos += 1
        body = text[m.start():pos]
        body = body.replace("int16_t bottom,top = cc_rwx+1;", "int16_t bottom;\n        int16_t top = cc_rwx+1;")
        body = re.sub(r"^(\s+)(?!static\b)((?:const )?(?:draw_column_vars_t|int16_t|fixed_t|boolean|subsector_t|seg_t|mapnode_t)\s+[^;{}\n]+;)",
                      r"\1static __xdata \2", body, flags=re.M)
        def static_init(match):
            indent, typ, var, expr = match.groups()
            return f"{indent}static __xdata {typ.replace('const ', '')}{var};\n{indent}{var} = {expr};"
        body = re.sub(r"^(\s+)static __xdata (.+?\s+)(\w+)\s*=\s*([^;\n]+);", static_init, body, flags=re.M)
        # In SDCC a qualifier before '*' changes the pointed-to address space.
        # Plain static locals already live in XDATA under --model-large and
        # retain the three-byte generic pointers required for DDR objects.
        body = body.replace("static __xdata ", "static ")
        text = text[:m.start()] + body + text[pos:]
    # The controller/render path uses only angle16 results. Drop the unused
    # angle32 entry point; exact high words remain in DDR for angle16 queries.
    text = function_replace(text,"R_PointToAngle3","")
    text = function_replace(text,"SlopeDiv","")
    text = re.sub(r"(tantoangle16Table\[.*)\*2\]",r"\1]",text)
    tables, initializers = [], []
    address = 0x10010
    for name, size in (("viewangletoxTable", 1), ("tantoangleTable", 4), ("finetangentTable_part_3", 2), ("finetangentTable_part_4", 4)):
        m = re.search(r"^static const (\w+)\s+" + name + r"\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.M | re.S)
        typ, values = m.groups()
        nums = [int(v.strip(), 0) for v in values.split(",") if v.strip()]
        raw = b"".join((v & ((1 << (size * 8)) - 1)).to_bytes(size, "little") for v in nums)
        (out / (name + ".bin")).write_bytes(raw)
        tables.append(dict(name=name, address=address, bytes=len(raw), hex=raw.hex()))
        # Preserve original table values for asset conversion and exact checks.
        definition=text[m.start():m.end()].replace("static const ","const __code ",1)
        code_type=typ
        if name=="tantoangleTable":
            code_type="uint16_t"
            definition="const __code uint16_t tantoangleTable[2049] = {"+",".join(str((n>>16)&65535) for n in nums)+"};"
        text = text[:m.start()] + definition + text[m.end():]
        text = re.sub(r"^static const " + typ + r"\s+" + name + r"\[[^\]]*\];",
                      "extern const __code " + code_type + " " + name + "[" + str(len(nums)) + "];",text,flags=re.M)
        if name in ("viewangletoxTable","finetangentTable_part_3","finetangentTable_part_4","tantoangleTable"):
            # Functionality first: make room for native sprites in bank zero.
            # Original exact table bytes already live in the DDR asset image.
            text = text.replace(definition, "static const " + code_type + " *" + name + ";")
            text = re.sub(r"^extern const __code " + code_type + r" " + name + r"\[[^\]]*\];",
                          "static const " + code_type + " *" + name + ";",text,flags=re.M)
            pointer_address=address
            if name=="tantoangleTable":
                high=b"".join(((n>>16)&65535).to_bytes(2,"little") for n in nums)
                pointer_address=0x1C0010
                tables.append(dict(name="tantoangle16",address=pointer_address,bytes=len(high),hex=high.hex()))
            initializers.append(f"{name} = DdrPointer(0x{pointer_address:X}UL);")
        address = (address + len(raw) + 15) & ~15
    # Angle16 indexes the packed uint16 table through the native DDR bridge.
    text = re.sub(r"^static const angle16_t\* tantoangle16Table.*$", "#define tantoangle16Table tantoangleTable", text, flags=re.M)
    text = text.replace("if (prevx == x && prevy == y)","if (prevr && prevx == x && prevy == y)")
    text = text.replace("static drawseg_t _s_drawsegs[128];", "static drawseg_t *_s_drawsegs;")
    text = re.sub(r"static int16_t openings\[\(\d+\*16\)\];", "static int16_t *openings;",text)
    text = text.replace("const uint8_t fullcolormap[256 * 34];", "const uint8_t *fullcolormap;")
    text = "#include \"platform.h\"\n" + text
    # A standalone native map-thing pass shares the actual wall drawseg clips.
    # It executes after BSP rendering, before the indexed framebuffer is shown.
    text = text.replace("void R_RenderPlayerView (player_t* player)",
                        "static void R_StaticSprites(void);\nvoid R_RenderPlayerView (player_t* player)")
    text = text.replace("    R_FreeSkyPatch ();", "    R_FreeSkyPatch ();\n    R_StaticSprites();")
    text=text.replace("static void R_RenderSegLoop(","void R_PlatformPlane(int16_t pic,int32_t height,int16_t light,const draw_column_vars_t *dc);\nstatic void R_RenderSegLoop(")
    text=text.replace("R_DrawColumnFlat(ceilingplane_color, &dcvars);","R_PlatformPlane(frontsector->ceilingpic,frontsector->ceilingheight,frontsector->lightlevel,&dcvars);")
    text=text.replace("R_DrawColumnFlat(floorplane_color, &dcvars);","R_PlatformPlane(frontsector->floorpic,frontsector->floorheight,frontsector->lightlevel,&dcvars);")
    text += "\n" + (ROOT/"fw/doom/sprites.inc").read_text()+"\n"+(ROOT/"fw/doom/actors.inc").read_text()+"\n"+(ROOT/"fw/doom/combat.inc").read_text()
    text += "\nvoid R_PlatformInit(void) {\n" + "\n".join(initializers) + """
_s_drawsegs = DdrPointer(0xB0010UL);
openings = DdrPointer(0xC0010UL);
fullcolormap = DdrPointer(0x170010UL);
}
"""
    (out / "renderer.c").write_text(text)
    # Keep the small per-column view-angle and sine tables in CODE.
    t = run([sdcc, *flags, "-E", out / "tables.c"])
    t = re.sub(r"^#line.*\n", "", t, flags=re.M)
    # Move the exact large sine quarter-wave into DDR to fit combat in bank 0.
    m=re.search(r"static const uint16_t finesineTable_part_1\[2048\]\s*=\s*\{(.*?)\};",t,re.S)
    nums=[int(v.strip(),0) for v in m.group(1).split(',') if v.strip()]
    raw=b''.join(n.to_bytes(2,'little') for n in nums)
    tables.append(dict(name="finesineTable_part_1",address=0x1B0010,bytes=len(raw),hex=raw.hex()))
    t=t[:m.start()]+"#include \"platform.h\"\n#define finesineTable_part_1 ((const uint16_t *)DdrPointer(0x1B0010UL))\n"+t[m.end():]
    # Only the approximate entry points are used by the native renderer/game.
    # Remove full-angle helpers; preserve all exact original half-step samples.
    for unused in ("finesine","finecosine","finesine_part_2","finesine_part_3","finesine_part_4","finecosine_part_4"):
        t=function_replace(t,unused,"")
    t=function_replace(t,"finesineapprox", """fixed_t finesineapprox(int16_t x) {
        uint16_t i=(uint16_t)x&4095U;
        fixed_t value;
        if(i>=2048)i=4095U-i;
        value=finesineTable_part_1[i];
        if(x&4096)return -value;
        return value;
    }""")
    t=function_replace(t,"finecosineapprox", """fixed_t finecosineapprox(int16_t x) {
        return finesineapprox((x+2048)&8191);
    }""")
    (out / "trig.c").write_text(t)
    (out / "tables.json").write_text(json.dumps(tables, indent=2))
    return tables


def build(sdcc, linker, libdir, out, cache_sdcc=None, width=60, height=128):
    if width not in (30,40,60,80,120,240) or height<16 or height>128 or height%16:
        raise ValueError("supported widths 30/40/60/80/120/240; heights 16..128 in steps of 16")
    cfg = cache_config(out,{"DOOM_VIEW_WIDTH":width,"DOOM_VIEW_HEIGHT":height})
    include_flag = "-I" + str(libdir.parent.parent / "include")
    flags = [*FLAGS,include_flag,f"-DVIEWWINDOWWIDTH={width}",f"-DDOOM_VIEW_WIDTH={width}",
             f"-DDOOM_VIEW_HEIGHT={height}",f"-DDOOM_RASTER_PITCH={cfg['DOOM_RASTER_PITCH']}"]
    tables = prepare(sdcc, out, flags, width, height)
    asm = ROOT / "fw/doom"
    for name in ("fixed_math", "ddr_pointer", "fixed_stack_abi", "gptr_cmp", "video", "cache_native", "projectile_bank"):
        assemble_runtime(sdcc,out,name)
    for src, name in ((out / "renderer.c", "renderer"), (out / "trig.c", "trig"),
                      (asm / "ddr_cache.c", "ddr_cache"), (asm / "renderer_port.c", "renderer_port"),
                      (asm / "motion.c", "motion"), (asm / "doors.c", "doors")):
        print("Compiling", name, flush=True)
        compile_flags = [f for f in flags if f != "--stack-auto"] + ["--sloc-xdata"] if name in ("ddr_cache",) else flags
        compiler = cache_sdcc or sdcc if name == "ddr_cache" else sdcc
        assemble_c(compiler, [*compile_flags, "-I" + str(out), "-I" + str(asm)], src, out / (name + ".rel"))
        # ABI zero is the stock SDCC ABI. Older sdld treats its explicit new
        # spelling as a conflict with libraries that omit the default marker.
        rel = out / (name + ".rel")
        rel.write_text(rel.read_text().replace(" sdcccall(0)", ""))
    objects = [out / (n + ".rel") for n in ("renderer_port", "renderer", "trig", "ddr_cache", "motion", "doors", "projectile_bank", "fixed_math", "fixed_stack_abi", "ddr_pointer", "gptr_cmp", "video", "cache_native")]
    run([linker, "-mmcs51", "--model-large", "--stack-auto", "--xram-loc", "0xD700", "--xram-size", "0x900",
         "--iram-size", "256", "--lib-path", libdir, *objects, "-o", out / "doom_renderer.ihx"])
    import doom_banks
    doom_banks.build(sys.modules[__name__],sdcc,linker,flags,out)
    return tables


def simulate(wad, out, *, yaw=None, latency=0, drop_every=0, frames=1, yaw_step=0, commands=None, initial_pose=None, input_provider=None, on_frame=None, save_frames=True, hud=True, scene=None, mapname="E1M1", packed=None):
    import fastmachine as F
    import ddr_sim as D
    import doom_sim as S
    import doom_assets
    import doom_motion as M
    from PIL import Image
    if not 1 <= frames <= 65535: raise ValueError("frames must be 1..65535")
    image = (out/"doom_renderer.bin").read_bytes() if (out/"banking.json").exists() else S.load_ihx(out / "doom_renderer.ihx")
    if (out/"banking.json").exists():
        import hashlib
        banking=json.loads((out/"banking.json").read_text())
        assert image[:65536]==S.load_ihx(out/"doom_renderer.ihx"),"bank-zero image differs from combined native image"
        if "image_sha256" in banking:assert hashlib.sha256(image).hexdigest()==banking["image_sha256"],"native bank image checksum mismatch"
    core = F.Core(image)
    model = json.loads(F.MODEL_JSON.read_text())
    core.set_dw(model)
    core.set_fetch(model)
    core.reset()
    cfg = cache_config(out)
    core.set_xpage_sfr(cfg["DOOM_SFR_MPAGE"])
    core.xram[0xFDA0] = 1
    core.L.core_set_fetch_ratio(core.h, 3 * 256)
    core.set_ddr(D.config(), latency_clk=latency)
    core.L.core_ddr_drop_every(core.h, 0, drop_every)
    try:
        if packed:
            if scene is not None or yaw is not None:raise ValueError('translated scenes use their packed pose and map data')
            boot,assets=doom_assets.load_native(packed,image,core.ddr_mem())
        else:
            boot, assets = doom_assets.pack(wad, image, core.ddr_mem(), out, mapname=mapname, yaw=yaw,**({'scene':scene} if scene is not None else {}))
        if initial_pose is not None:
            boot=boot[:50]+struct.pack("<iiIi",initial_pose["x"],initial_pose["y"],initial_pose["angle"],initial_pose["viewz"])+boot[66:]
        initial_health=[]
        if (assets.get("monsters") or {}).get("combat"):
            initial_health=[struct.unpack_from("<H",core.ddr_mem(),0xD0020+i*20+18)[0] or 20 for i in range(assets["monsters"]["count"])]
        core.xram[0xF640:0xF640+len(boot)] = boot
        core.xram[0xF71E]=int(bool(hud))
        def set_command(index):
            command=input_provider(index) if input_provider else (commands[index] if commands else dict(enabled=0))
            core.xram[M.INPUT_BASE:M.INPUT_BASE+M.INPUT.size]=M.pack_command(command)
        if commands is not None and len(commands)!=frames: raise ValueError("one command required per frame")
        set_command(0)

        core.xram[0xF630] = frames&255
        core.xram[0xF632] = frames>>8
        core.xram[0xF634:0xF638] = (int(yaw_step * (1 << 32) / 360) & 0xFFFFFFFF).to_bytes(4,"little")
        core.hook(1, 0xF600)  # EV_XW: stop after the actual native status write.
        started = time.monotonic()
        stages = {}
        phase_clocks = {}
        completed = []
        stopped=False
        last_clk = 0
        startup_clk = 0
        last_stats = dict.fromkeys(("writes","reads","invalid","hazards","dropped"),0)
        width,height=cfg["DOOM_VIEW_WIDTH"],cfg["DOOM_VIEW_HEIGHT"]
        for _ in range(10000 * frames):
            reason = core.run(100000)
            state = core.xram[0xF600]
            if reason == F.R_EVENT:
                stages.setdefault(str(state), core.p.clk)
                if state in (2,3,4): phase_clocks[state] = core.p.clk
            if core.p.sp_wrap:
                raise AssertionError(f"8051 stack wrapped at PC {core.p.pc:04X}")
            if reason not in (F.R_DONE, F.R_PC, F.R_EVENT):
                raise AssertionError(f"core stopped: {reason}, PC {core.p.pc:04X}")
            if state not in (0xA4, 0xA5) or reason != F.R_EVENT: continue
            status = list(core.xram[0xF600:0xF610])
            stats = core.ddr_stats()
            assert core.p.bank==0,"native projectile bank was not restored"
            assert status[1] == 0 and stats["invalid"] == stats["hazards"] == 0, (status, stats)
            assert "3" in stages, "renderer did not return through its expected caller"
            raster = D.DdrMemory()
            raster.core = core
            frame = raster.raster(width, height, base=cfg["DOOM_RASTER_BASE"], pitch=cfg["DOOM_RASTER_PITCH"])
            # Independent oracle: the CPU decides all scene pixels and converts
            # them to RGB. Host work validates/captures completed frames only.
            ram = core.ddr_mem()
            palette = bytes(ram[0x180010:0x180310])
            columns = bytes(ram[cfg["DOOM_INDEXED_BASE"]:cfg["DOOM_INDEXED_BASE"]+width*cfg["DOOM_TEXTURE_COLUMN_SIZE"]])
            indexed = bytes(columns[x*cfg["DOOM_TEXTURE_COLUMN_SIZE"]+y] for y in range(height) for x in range(width))
            expected = b"".join(palette[c*3:c*3+3] for c in indexed)
            assert frame.tobytes() == expected, "8051 palette conversion mismatch"
            # A close wall can legitimately fill the view with one palette index.
            elapsed = core.p.clk-last_clk
            if not completed:
                startup_clk = phase_clocks[2]
                elapsed -= startup_clk
            world_verified=M.verify_profiles(core.ddr_mem(),assets)
            motion_profiles=M.read_profiles(core.ddr_mem(),assets["motion"]["lines"])
            doors=M.read_doors(core.xram)
            motion=M.unpack_state(core.xram[M.STATE_BASE:M.STATE_BASE+M.STATE.size])
            motion_verified=M.validate_pose(motion,motion_profiles,completed[-1]["motion"] if completed else None) if motion["enabled"] else None
            sprite_state=dict(zip(("loaded","candidates","projected","pixels"),struct.unpack("<4H",core.xram[0xF6D0:0xF6D8]))) if assets.get("monsters") else None
            actors=None
            if (assets.get("monsters") or {}).get("animated"):
                actor_has_health=(assets.get("monsters") or {}).get("combat",False)
                actor_rows=struct.iter_unpack("<hhHHiHBBhH",ram[0xD0020:0xD0020+assets["monsters"]["count"]*20])
                actors=dict(stats=dict(zip(("ticks","moves","blocked","awake"),struct.unpack("<4H",core.xram[0xF6E0:0xF6E8]))),
                            things=[dict(zip(("x","y","angle","kind","depth","tics","frame","awake","floor","health" if actor_has_health else "reserved"),row)) for row in actor_rows])
                actors["verified"]=True
                previous_actors=completed[-1]["actors"]["things"] if completed else None
                for ai,actor in enumerate(actors["things"]):
                    if not actor["awake"] or (actor_has_health and not actor["health"]):continue
                    M.validate_pose(dict(x=actor["x"]*65536,y=actor["y"]*65536,floor=actor["floor"],ceiling=32767,fault=0),motion_profiles)
                    if previous_actors:
                        before=previous_actors[ai]
                        assert abs(actor["x"]-before["x"])<=4 and abs(actor["y"]-before["y"])<=4,"actor movement exceeded native per-frame budget"
                        if (actor["x"],actor["y"])!=(before["x"],before["y"]):
                            assert abs(actor["x"]-(motion["x"]>>16))>=32 or abs(actor["y"]-(motion["y"]>>16))>=32,"actor entered player body"
            projectiles=None
            if (assets.get("monsters") or {}).get("projectiles"):
                slots=[]
                for pi in range(8):
                    row=struct.unpack_from("<hhHHiHBBhH",ram,0xD0020+(assets["monsters"]["count"]+pi)*20)
                    fx,fy,vx,vy,age,owner=struct.unpack_from("<iihhHH",ram,0xD6010+pi*16)
                    slots.append(dict(x=row[0],y=row[1],z=row[8],frame=row[6],phase=row[7],active=bool(row[9]),fx=fx,fy=fy,vx=vx,vy=vy,age=age,owner=owner))
                for slot in slots:
                    if slot["active"] and slot["phase"]==1:
                        assert (slot["fx"]>>16,slot["fy"]>>16)==(slot["x"],slot["y"]),"native projectile position mismatch"
                        assert 0<max(abs(slot["vx"]),abs(slot["vy"]))<=2048,"invalid native fireball speed"
                if completed and completed[-1].get("projectiles"):
                    for before,slot in zip(completed[-1]["projectiles"]["slots"],slots):
                        if before["active"] and slot["active"] and before["phase"]==slot["phase"]==1 and before["owner"]==slot["owner"] and slot["age"]>=before["age"]:
                            dt=slot["age"]-before["age"]
                            assert (slot["fx"],slot["fy"])==(before["fx"]+slot["vx"]*256*dt,before["fy"]+slot["vy"]*256*dt),"native fireball trajectory mismatch"
                ps=dict(zip(("spawned","substeps","walls","hits","reserved","expired","dropped","visited"),struct.unpack("<8H",core.xram[0xF720:0xF730])))
                assert ps["spawned"]-ps["walls"]-ps["hits"]-ps["expired"]==sum(s["active"] and s["phase"]==1 for s in slots),"native fireball accounting mismatch"
                projectiles=dict(stats=ps,slots=slots,verified=True)
            combat=None
            pickups=None
            pickup_assets=(assets.get('monsters') or {}).get('pickups') or {}
            if pickup_assets.get('enabled'):
                ps=dict(zip(('collected','health_added','ammo_added','flash'),struct.unpack('<4H',core.xram[0xF740:0xF748])))
                items=[]
                for pi,original in enumerate(pickup_assets['things']):
                    row=struct.unpack_from('<hhHHiHBBhH',ram,0xD0020+(assets['monsters']['count']+8+pi)*20)
                    assert (row[0],row[1],row[3],row[5])==(original['x'],original['y'],original['kind'],original['rule']), 'native pickup moved or changed kind'
                    assert row[9] in (0,1), 'invalid native pickup active flag'
                    items.append(dict(x=row[0],y=row[1],floor=row[8],kind=row[3],rule=row[5],active=bool(row[9])))
                assert ps['collected']==sum(not p['active'] for p in items),'native pickup consumption accounting mismatch'
                assert ps['flash']<=5
                assert ps['health_added']<=sum({0:10,1:25,2:1}.get(p['rule'],0) for p in items if not p['active'])
                assert ps['ammo_added']<=sum({3:10,4:50}.get(p['rule'],0) for p in items if not p['active'])
                previous=completed[-1].get('pickups') if completed else None
                for pi,p in enumerate(items):
                    before=previous['items'][pi] if previous else dict(active=True)
                    assert before['active'] or not p['active'], 'collected native pickup reappeared'
                    if before['active'] and not p['active']:
                        assert abs(p['x']-(motion['x']>>16))<=20 and abs(p['y']-(motion['y']>>16))<=20, 'remote native pickup collected'
                        assert -8<=p['floor']-motion['floor']<=56, 'native pickup collected at wrong height'
                pickups=dict(stats=ps,items=items,verified=True)
            inventory=None
            if image[0xFFF0:0xFFF4]==b'D805' and image[0xFFF4]>=7:
                inventory=dict(zip(('keys','needed','denied','notice'),struct.unpack('<4H',core.xram[0xF748:0xF750])))
                expected_keys=0
                for p in pickups['items'] if pickups else []:
                    if p['rule']>=5 and not p['active']:expected_keys|=1<<(p['rule']-5)
                assert inventory['keys']==expected_keys,'native key inventory does not match collected items'
                assert inventory['keys']<64 and inventory['needed'] in (0,1,2,4) and inventory['notice']<=35
                inventory['verified']=True
            switches=None
            if 'switches' in assets:
                ss=dict(zip(('activations','resets','consumed','last'),struct.unpack('<4H',core.xram[0xF750:0xF758])))
                timers=list(core.xram[0xF760:0xF760+len(assets['switches'])])
                assert ss['consumed']<1<<len(timers) and ss['last']<=len(timers)
                for si,definition in enumerate(assets['switches']):
                    assert timers[si]<=35
                    if definition['texture']:
                        tex=struct.unpack_from('<h',ram,definition['texture'])[0]
                        assert tex==(definition['on'] if timers[si] or ss['consumed']&(1<<si) else definition['off']),'native switch texture mismatch'
                previous=completed[-1].get('switches') if completed else None
                old_activations=previous['stats']['activations'] if previous else 0
                if ss['activations']>old_activations:
                    definition=assets['switches'][ss['last']-1]
                    before=completed[-1]['doors']['activations'] if completed else 0
                    assert doors['activations']-before==definition['mask'].bit_count(),'native switch target activation mismatch'
                switches=dict(stats=ss,timers=timers,verified=True)
            if image[0xFFF0:0xFFF4]==b"D805":
                raw=struct.unpack("<8H4BH",core.xram[0xF700:0xF716])
                combat=dict(zip(("health","ammo","shots","hits","kills","damage","attacks","dead","wait","flash","hurt","spare","target"),raw))
                assert combat["ammo"]+combat["shots"]==50+(pickups['stats']['ammo_added'] if pickups else 0),"native ammunition accounting mismatch"
                assert combat["hits"]<=combat["shots"] and combat["kills"]<=combat["hits"]
                assert combat["health"]==max(0,100+(pickups['stats']['health_added'] if pickups else 0)-combat["damage"]),"native player damage mismatch"
                assert combat['health']<=200 and combat['ammo']<=200
                assert bool(combat["dead"])==(combat["health"]==0)
                if actors is not None:
                    assert sum((h+19)//20-(t["health"]+19)//20 for h,t in zip(initial_health,actors["things"]))==combat["hits"],"native actor damage accounting mismatch"
                    assert all(0<=t['health']<=h and (not t['health'] or (h-t['health'])%20==0) for h,t in zip(initial_health,actors['things'])),"native actor damage step mismatch"
                    assert sum(t["health"]==0 for t in actors["things"])==combat["kills"],"native kill accounting mismatch"
                combat["verified"]=True
            exit_state=None
            if image[0xFFF0:0xFFF4]==b'D805' and image[0xFFF4]>=9:
                exit_state=dict(zip(('kind','line','activations','reserved'),struct.unpack('<4H',core.xram[0xF770:0xF778])))
                assert exit_state['kind'] in (0,1,2) and exit_state['activations']==bool(exit_state['kind'])
                if exit_state['kind']:
                    assert any(s['line']==exit_state['line'] and s['kind']==exit_state['kind'] for s in assets['switches']),'native exit does not match a packed exit line'
                    assert combat['health']>0
                if completed and completed[-1].get('exit',{}).get('kind'):
                    before=completed[-1]
                    for key,value in (('combat',combat),('actors',actors),('projectiles',projectiles),('pickups',pickups),('inventory',inventory),('switches',switches),('doors',doors),('exit',exit_state)):
                        assert before[key]==value,'game state advanced after native exit: '+key
                    assert all(before['motion'][k]==motion[k] for k in ('x','y','angle','floor','ceiling','ticks')),'player moved after native exit'
            completed.append(dict(cpu_clk=elapsed,model_ms=elapsed*1000/S.CPU_HZ,sprites=sprite_state,actors=actors,combat=combat,projectiles=projectiles,pickups=pickups,inventory=inventory,switches=switches,exit=exit_state,
                                  doors=doors,world_verified=world_verified,motion=motion,motion_verified=motion_verified,motion_clk=phase_clocks[4]-phase_clocks[2],
                                  render_clk=phase_clocks[3]-phase_clocks[2],
                                  present_flush_clk=core.p.clk-phase_clocks[3],
                                  ddr={k:stats[k]-last_stats[k] for k in stats},
                                  palette_indices=len(set(indexed))))
            last_clk, last_stats = core.p.clk, stats
            if frames > 1 and save_frames: frame.save(out/f"frame-{len(completed)-1:03d}.png")
            if on_frame and on_frame(frame,completed[-1],len(completed)-1) is False:
                stopped=True
                break
            if state == 0xA5: break
            set_command(len(completed))
            core.xram[0xF631] = 1
        else:
            raise AssertionError(f"renderer instruction budget exhausted at {core.p.pc:04X}")
        assert stopped or len(completed) == frames, "firmware completed a different frame count"
        frame.save(out / "e1m1-native.png")
        preview = frame.resize((480,256), Image.Resampling.NEAREST)
        preview.save(out / "e1m1-preview.png")
        result = dict(assets=assets, hud=bool(hud and (assets.get("monsters") or {}).get("combat")),width=width,height=height,instructions=core.p.instr, cpu_clk=core.p.clk,
                      cpu_hz=S.CPU_HZ, model_ms=core.p.clk*1000/S.CPU_HZ,bank_switches=int(core.cnt[4]),banking=json.loads((out/"banking.json").read_text()) if (out/"banking.json").exists() else None,
                      stack_high=core.p.sp_max, stack_wraps=core.p.sp_wrap,
                      ddr=stats, ddr_latency_clk=latency, ready_drop_every=drop_every,
                      host_seconds=time.monotonic()-started, stages=stages,
                      palette_verified=True,
                      palette_indices=len(set(indexed)),
                      frames=completed, stopped=stopped,
                      start_yaw=yaw, yaw_step=yaw_step, initial_pose=initial_pose,
                      startup_clk=startup_clk, startup_ms=startup_clk*1000/S.CPU_HZ,
                      max_frame_ms=max(f["model_ms"] for f in completed),
                      timing="Frame zero starts after one-time initialization. Later complete frame intervals include native control/advance overhead. Every frame includes enabled native movement, indexed clearing, rendering, RGB conversion, DDR writes and flush. Total model_ms includes startup. Host capture pauses consume no simulated CPU clocks.",
                      min_equivalent_fps=1000/max(f["model_ms"] for f in completed),
                      scope="Native Doom8088 BSP/wall renderer with animated ground monsters. Textured native planes/sky; standalone movement/collision and manual doors. Native sight/chase, pistol combat, soldier ranged shots, imp fireballs, health/ammo pickups and HUD. No original game thinkers. Ideal DDR unless specified; not measured hardware FPS.")
        (out / "renderer-results.json").write_text(json.dumps(result, indent=2)+"\n")
        return result, preview
    finally:
        core.free()


def capture_stream(frame, out):
    import io
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from sim_live import Stream, LATEST
    buf = io.BytesIO()
    frame.save(buf, "JPEG", quality=95)
    LATEST["jpg"] = buf.getvalue()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Stream)
    url = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(url + "/frame.jpg", timeout=5) as response:
            jpeg = response.read()
        assert jpeg.startswith(b"\xff\xd8")
        (out / "vlc-frame.jpg").write_bytes(jpeg)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "mpjpeg", "-r", "4", "-i", url+"/stream",
             "-t", "1", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out/"vlc-capture.mp4"], timeout=30)
        return dict(validated=True, video="vlc-capture.mp4", jpeg_bytes=len(jpeg), scope="One native-rendered still served through sim_live MJPEG; not gameplay or an FPS measurement.")
    finally:
        server.shutdown()
        server.server_close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sdcc", type=Path, required=True)
    p.add_argument("--linker", type=Path, help="SDCC driver for the matching installed assembler/linker")
    p.add_argument("--cache-sdcc", type=Path, help="optional awto-sdcc compiler for the cache register ABI")
    p.add_argument("--libdir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "tmp/doom-renderer")
    p.add_argument("--width",type=int,default=60)
    p.add_argument("--height",type=int,default=128)
    p.add_argument("--wad", type=Path, help="original Doom 1 shareware IWAD, not preprocessed")
    p.add_argument("--map",default="E1M1",help="original map marker, e.g. E1M6")
    p.add_argument("--packed",type=Path,help="translated native map folder; no IWAD needed")
    p.add_argument("--yaw", type=int, help="camera angle in degrees; defaults to player start")
    p.add_argument("--latency", type=int, default=0, help="additional DDR command clocks")
    p.add_argument("--drop-every", type=int, default=0, help="drop every nth read ready")
    p.add_argument("--pose",type=Path,help="optional initial native fixed-point x/y/angle/viewz JSON")
    p.add_argument("--scene",type=Path,help="explicit initial demonstration edits; never live gameplay")
    p.add_argument("--commands",type=Path,help="JSON list of per-frame forward/strafe/turn commands")
    p.add_argument("--frames",type=int,default=1)
    p.add_argument("--yaw-step",type=float,default=0)
    p.add_argument("--skip-build", action="store_true")
    p.add_argument("--capture-stream", action="store_true", help="check sim_live MJPEG with ffmpeg and save VLC-compatible MP4")
    a = p.parse_args()
    a.out.mkdir(exist_ok=True, parents=True)
    if not a.skip_build:
        build(a.sdcc.absolute(), (a.linker or a.sdcc).absolute(), a.libdir.resolve(), a.out.resolve(), a.cache_sdcc.absolute() if a.cache_sdcc else None,a.width,a.height)
    print(a.out / ("doom_renderer.bin" if (a.out/"banking.json").exists() else "doom_renderer.ihx"))
    if a.wad or a.packed:
        commands=json.loads(a.commands.read_text()) if a.commands else None
        result, frame = simulate(a.wad, a.out, mapname=a.map, packed=a.packed, yaw=a.yaw, latency=a.latency, drop_every=a.drop_every, frames=len(commands) if commands else a.frames, yaw_step=a.yaw_step, commands=commands,initial_pose=json.loads(a.pose.read_text()) if a.pose else None,scene=json.loads(a.scene.read_text()) if a.scene else None)
        if a.capture_stream:
            result["vlc"] = capture_stream(frame, a.out)
            (a.out/"renderer-results.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
