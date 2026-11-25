#!/usr/bin/env python3
"""Arcade image of awto-games-dw8051: Pac-Man, Asteroids and Scope 2 as awto-ddc extra apps (docs/arcade-image.md).

usage: arcade.py build              generate local data, then `ddc/dev.py build --extra-fw fw/games --tag arcade`
       arcade.py sim [--game NAME]  run the built image in the firmware simulator (scripts/arcade_sim.py)
       arcade.py budget             bank / XDATA / IRAM budget of the built image -> docs/arcade-budget.tsv (scripts/arcade_budget.py)
Builds go through ddc/dev.py only (awto-ddc submodule, `git submodule update --init`). No flashing, no hardware.
Log: ./tmp/logs/arcade.log
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from _repo import repo_root  # noqa: E402

ROOT = repo_root()
DDC = ROOT / "ddc"
SCRIPTS = ROOT / "scripts"
EXTRA_FW = ROOT / "fw/games"
TAG = "arcade"
APP_MODULES = ["pacman_classic", "asteroids", "scope_saver2", "arcade_snd", "saver_canvas", "apps"]     # compiled modules of the arcade apps + the awto-ddc hook framework
LOG = ROOT / "tmp/logs/arcade.log"
BUILD_STALL_S = 60          # no output line for this long = hung (global rule: host build stall guard); first compile line ~ 10 s


def say(msg: str) -> None:
    sys.path.insert(0, str(DDC / "scripts"))
    from _log import log_line
    log_line(msg, LOG)


def env() -> dict:
    e = os.environ.copy()
    e["PYTHONPATH"] = os.pathsep.join([str(SCRIPTS), str(DDC / "scripts"), e.get("PYTHONPATH", "")])
    e["AWTO_DDC_REPO"] = str(DDC)
    return e


def run(cmd: list, cwd: Path) -> int:
    """Run with output teed to the log; kill when no output line arrives for BUILD_STALL_S."""
    import selectors
    say("run: " + " ".join(map(str, cmd)))
    p = subprocess.Popen(cmd, cwd=cwd, env=env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    last = ""
    while p.poll() is None:
        if not sel.select(BUILD_STALL_S):
            p.kill()
            say(f"STALL: no output for {BUILD_STALL_S} s, killed; last line: {last!r}")
            return 1
        line = p.stdout.readline()
        if line:
            last = line.rstrip()
            say("  " + last)
    for line in p.stdout.read().splitlines():
        say("  " + line)
    return p.returncode


def save_modules() -> None:
    """tmp/arcade_modules.tsv: module <TAB> chunk name from the post-bank asm of the build that just ran (the next build overwrites it)."""
    import re
    rows = []
    for m in APP_MODULES:
        asm = DDC / "tmp/sdcc-port/asm_bank" / f"{m}.asm"
        rows += [f"{m}\t{c[2:]}\n" for c in re.findall(r"^\s*\.area (CH\S+)", asm.read_text(errors="replace"), re.MULTILINE)]
    (ROOT / "tmp/arcade_modules.tsv").write_text("".join(rows))


def cmd_build(release: bool = False) -> int:
    if not (DDC / "dev.py").is_file():
        say("ddc/ is empty: git submodule update --init ddc")
        return 1
    rc = run([sys.executable, str(SCRIPTS / "gen_asteroids.py"), "--fallback"], ROOT)     # shapes: own outlines, never ROM data
    if rc:
        return rc
    cmd = [sys.executable, str(DDC / "dev.py"), "build", "--extra-fw", str(EXTRA_FW), "--tag", TAG + ("-rel" if release else "")]
    rc = run(cmd + (["--layout", "release"] if release else []), DDC)
    if rc == 0 and not release:
        save_modules()
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--release", action="store_true", help="release layout (fewest banks), tag arcade-rel: the numbers for the Doom bank plan")
    s = sub.add_parser("sim")
    s.add_argument("--game", default="")
    sub.add_parser("budget")
    a, rest = ap.parse_known_args()
    if a.cmd == "build":
        return cmd_build(a.release)
    mod = {"sim": "arcade_sim.py", "budget": "arcade_budget.py"}[a.cmd]
    extra = ["--game", a.game] if a.cmd == "sim" and a.game else []
    return run([sys.executable, str(SCRIPTS / mod), *extra, *rest], ROOT)


if __name__ == "__main__":
    sys.exit(main())
