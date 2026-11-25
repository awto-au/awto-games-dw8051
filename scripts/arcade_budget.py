#!/usr/bin/env python3
"""Bank / XDATA / IRAM budget of the arcade image -> docs/arcade-budget.tsv (internal module of arcade.py budget).

usage: arcade_budget.py [--stem tmp/fw/<stem>] [--base tmp/fw/<stem>] [--out docs/arcade-budget.tsv]
  - Reads the build's frozen files (<stem>.bank_layout.tsv, .xdata_layout.tsv, .xdata.json, .apps.tsv) + tmp/arcade_modules.tsv (module, chunk name; written by `arcade.py build`).
  - Rows (columns: scope name bank code const stub total capacity free note):
      bank  = per code bank 0..14: bytes of fn / const / stub chunks in the image, capacity (bank size - common - reserved msg block), free;
              `base` = the same image built without --extra-fw (default awto-ddc image), `games` = the arcade chunks in the bank
      game  = per game module group: chunk bytes by kind, banks they sit in, banks pinned in the source (#pragma place bank)
      xdata = XDATA slot per game module (fw/xdata_layout.tsv rows) + pool free of the image / base
      iram  = fw_ram_report row of the image (direct IRAM free, data used, stack)
      doom  = the Doom format-10 image (artifacts/current) against the release layout: banks, unique bytes, banks left
  - Exit 1 when a pinned chunk sits in another bank or the last build is not the arcade image.
Log: ./tmp/logs/arcade_budget.log
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DDC = ROOT / "ddc"
sys.path.insert(0, str(DDC / "scripts"))
from _log import log_line as _log_line  # noqa: E402
import chip_mem as CM  # noqa: E402

LOG = ROOT / "tmp/logs/arcade_budget.log"
STEM = DDC / "tmp/fw/AWT26110001-arcade-be"
BASE = DDC / "tmp/fw/AWT26110001-base-ref-be"           # the default image (`ddc/dev.py build --tag base-ref`), optional
REL = DDC / "tmp/fw/AWT26110001-arcade-rel-be"           # `arcade.py build --release`, optional
MODULES = ROOT / "tmp/arcade_modules.tsv"
GAMES_DIR = ROOT / "fw/games"
BANK_CAP = CM.BANK_SIZE - CM.COMMON_END                         # bytes of one code bank above the common region
MSG_BANK = next(a // CM.BANK_SIZE for a, _ in CM.RESERVED.values())
MSG_BYTES = sum(s for _, s in CM.RESERVED.values())
COLS = ["scope", "name", "bank", "code", "const", "stub", "total", "capacity", "free", "note"]
# game group -> (compiled modules, source files scanned for `#pragma place bank(N)`)
GAMES = {
    "pacman": (["pacman_classic"], ["pacman_classic.c", "pacman_classic_data.inc"]),
    "asteroids": (["asteroids"], ["asteroids.c", "asteroids_data.inc"]),
    "scope2": (["scope_saver2"], ["scope_saver2.c", "scope2_data.inc"]),
    "sound": (["arcade_snd"], ["arcade_snd.c", "arcade_snd_data.inc"]),
    "canvas": (["saver_canvas"], ["saver_canvas.c"]),
    "apps": (["apps"], []),                                     # awto-ddc fw/apps/apps.c: the hook framework, in every --extra-fw image
}
PIN = re.compile(r"#pragma place bank\((\d+)\)")


def say(s: str) -> None:
    _log_line(s, LOG)


def layout(stem: Path) -> dict:
    out = {}
    for ln in Path(str(stem) + ".bank_layout.tsv").read_text().splitlines():
        f = ln.split("\t")
        if len(f) == 5 and not ln.startswith("#"):
            out[(f[0], f[1])] = (f[2], int(f[4]))
    return out


def bank_used(lay: dict) -> dict:
    u = collections.defaultdict(lambda: collections.Counter())
    for (k, _), (r, s) in lay.items():
        if r != "C" and k in ("fn", "const", "stub"):
            u[int(r)][k] += s
    return u


def doom_rows(rel: Path) -> list:
    """Doom image (format 10, artifacts/current) vs the release arcade image: whole 64 KiB banks, bytes that differ between them."""
    img = (ROOT / "artifacts/current/doom_renderer.bin").read_bytes()
    bk = [img[i * CM.BANK_SIZE:(i + 1) * CM.BANK_SIZE] for i in range(len(img) // CM.BANK_SIZE)]
    nz = [sum(1 for x in b if x != 0xFF) for b in bk]
    delta = [sum(1 for x, y in zip(bk[0], b) if x != y) for b in bk[1:]]
    info = json.loads((ROOT / "artifacts/current/banking.json").read_text())
    rows = [["doom", "image", len(bk), "", "", "", len(img), "", "", f"{len(bk)} banks of {CM.BANK_SIZE} B; non-0xFF per bank {nz}; common_end {info['common_end']}, overlay {info['overlay_start']}..{info['overlay_end']}"],
            ["doom", "unique", "", "", "", "", nz[0] + sum(delta), "", "", f"bank 0 non-0xFF {nz[0]} + bytes differing from bank 0 in banks 1..{len(bk) - 1}: {delta}"]]
    meta = Path(str(rel) + ".build.json")
    if meta.is_file():
        used = json.loads(meta.read_text())["image_bytes"] // CM.BANK_SIZE
        rows.append(["doom", "release_fit", f"{used}..{used + len(bk) - 1}", "", "", "", "", CM.CODE_BANKS, CM.CODE_BANKS - used - len(bk),
                     f"arcade release image ends with bank {used - 1} ({used} banks); Doom in banks {used}..{used + len(bk) - 1}; free = code banks {CM.CODE_BANKS} - {used} - {len(bk)}; bank {CM.CODE_BANKS} = NVRAM / manifest"])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stem", type=Path, default=STEM)
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--rel", type=Path, default=REL)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/arcade-budget.tsv")
    a = ap.parse_args()
    last = (a.stem.parent / (a.stem.name.split("-")[0] + "-last.txt")).read_text().strip()
    if not last.endswith(a.stem.name) or not MODULES.is_file():
        say(f"last build is {last!r}, not {a.stem.name}, or {MODULES} missing: run `arcade.py build` first")
        return 1
    lay = layout(a.stem)
    used = bank_used(lay)
    base_used = bank_used(layout(a.base)) if Path(str(a.base) + ".bank_layout.tsv").is_file() else None
    rel_used = bank_used(layout(a.rel)) if Path(str(a.rel) + ".bank_layout.tsv").is_file() else None
    chunks = collections.defaultdict(set)
    for ln in MODULES.read_text().splitlines():
        m, c = ln.split("\t")
        chunks[m].add(c)
    rows, bad = [], 0
    game_banks = collections.defaultdict(lambda: collections.Counter())     # bank -> game -> bytes
    for g, (mods, srcs) in GAMES.items():
        names = set().union(*(chunks[m] for m in mods))
        agg = collections.defaultdict(lambda: collections.Counter())          # kind -> bank -> bytes
        for (k, n), (r, s) in lay.items():
            callee = re.sub(r"^\d+_", "", n) if k == "stub" else n         # a local stub copy is named <bank>__<fn>
            if k in ("fn", "const", "stub") and callee in names and r != "C":
                agg[k][int(r)] += s
                game_banks[int(r)][g] += s
        banks = sorted(set(agg["fn"]) | set(agg["const"]))
        stub_banks = sorted(agg["stub"])
        pins = sorted({int(p) for s in srcs for p in PIN.findall((GAMES_DIR / s).read_text())})
        fn_banks = sorted(agg["fn"]) + sorted(agg["const"])
        off_pin = [b for b in set(fn_banks) if pins and b not in pins]
        if off_pin and g != "apps":
            say(f"{g}: chunks in bank(s) {off_pin}, pinned to {pins}")
            bad += 1
        tot = {k: sum(v.values()) for k, v in agg.items()}
        rows.append(["game", g, "+".join(map(str, banks)), tot.get("fn", 0), tot.get("const", 0), tot.get("stub", 0), sum(tot.values()), "", "",
                     f"pinned bank {'+'.join(map(str, pins)) or 'none (floats)'}; local stubs in bank {'+'.join(map(str, stub_banks)) or '-'}; modules {','.join(mods)}; {len(names)} chunks"])
    for b in range(CM.CODE_BANKS):
        cap = BANK_CAP - (MSG_BYTES if b == MSG_BANK else 0)
        u = used[b]
        tot = sum(u.values())
        gs = ", ".join(f"{g} {n}" for g, n in sorted(game_banks[b].items(), key=lambda x: -x[1]))
        bu = sum(base_used[b].values()) if base_used else ""
        rows.append(["bank", f"bank {b}", b, u["fn"], u["const"], u["stub"], tot, cap, cap - tot,
                     f"base {bu}" + (f"; release {sum(rel_used[b].values())}" if rel_used else "") + (f"; games: {gs}" if gs else "") + ("; msg block reserved" if b == MSG_BANK else "")])
    xl = {}
    for ln in Path(str(a.stem) + ".xdata_layout.tsv").read_text().splitlines():
        f = ln.split("\t")
        if len(f) == 4 and not ln.startswith("#"):
            xl[f[0]] = (f[1], int(f[3]))
    for g, (mods, _) in GAMES.items():
        slots = [(m, xl[m]) for m in mods if m in xl]
        rows.append(["xdata", g, "", "", "", "", sum(s for _, (_, s) in slots), "", "", ", ".join(f"{m} slot {s} B in hole {h}" for m, (h, s) in slots)])
    xj = json.loads(Path(str(a.stem) + ".xdata.json").read_text())
    bj = json.loads(Path(str(a.base) + ".xdata.json").read_text()) if Path(str(a.base) + ".xdata.json").is_file() else {}
    rows.append(["xdata", "pool", "", "", "", "", xj["xdata_pool"] - xj["xdata_free"], xj["xdata_pool"], xj["xdata_free"],
                 f"free in the image; base free {bj.get('xdata_free', 'n/a')}"])
    rep = subprocess.run([sys.executable, str(DDC / "scripts/fw_ram_report.py"), "--img", str(a.stem), "--build", str(DDC / "tmp/fw/AWT26110001/build.json"),
                          "--asm", str(DDC / "tmp/sdcc-port/asm_bank")], capture_output=True, text=True, cwd=DDC, check=False)
    cells = [c.strip() for c in rep.stdout.strip().splitlines()[-1].strip("|").split("|")] if rep.returncode == 0 else []
    if cells:
        h = [c.strip() for c in rep.stdout.strip().splitlines()[0].strip("|").split("|")]
        d = dict(zip(h, cells))
        rows.append(["xdata", "window", "", "", "", "", d["xdata_used"], "", d["xdata_free"], "XDATA window 0xE780..0xF6D0 (fw_ram_report)"])
        rows.append(["iram", "direct", "", "", "", "", d["data_used"], "", d["free_direct"], f"free direct IRAM; stack {d['stack_bytes']} B; iseg {d['iseg']}"])
    else:
        say("fw_ram_report failed: " + rep.stderr.strip()[-300:])
    rows += doom_rows(a.rel)
    a.out.write_text("\t".join(COLS) + "\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows))
    for r in rows:
        say("  " + "\t".join(map(str, r)))
    say(f"budget -> {a.out}; {bad} pin violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
