#!/usr/bin/env python3
"""Arcade image (fw/games, `arcade.py build`) in the firmware simulator: start each app by VCP 0xEB, run, measure, stop. No hardware.

usage: arcade_sim.py [BIN MAP] [--game NAME] [--seconds S] [--out DIR] [--rotate]   (internal module of arcade.py sim)
  - Per app: VCP 0xEB = 0x20 + index starts it; progress counter (game step / frame) read by map symbol; machine cycles per main-loop pass
    (core cycles / heartbeat) with the app running and with no app; OSD snapshot PNG; sound tone seconds + pitch events (audio_sim tap);
    MENU key stops it (key hook), then VCP 0 / the debug byte are not exercised here (awto-ddc scripts/apps_sim.py does that).
  - Cycles are sim machine cycles of the DW8051 model, not hardware time; an idle main loop (no app) paces itself, a running app free-runs
    the loop (AwtoLoopBusy), so the no-app baseline (logged) is not a floor for the app rows. Values are reported, no pass / fail limits.
Results: DIR/arcade_sim.tsv (default tmp/arcade_sim); log ./tmp/logs/arcade_sim.log
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ddc/scripts"))
os.environ.setdefault("AWTO_SIM_CORE", "fast")
from _log import log_line as _log_line  # noqa: E402

import audio_sim as A  # noqa: E402
import ddc_sim as D  # noqa: E402
import osd_render as R  # noqa: E402

ROOT = HERE.parent                      # this repo; ddc/scripts' own _repo (ROOT = ddc) stays first on sys.path for the sim modules
LOG = ROOT / "tmp/logs/arcade_sim.log"
DDC_FW = ROOT / "ddc/tmp/fw"
STEM = "AWT26110001-arcade-be"          # serial of the dev build (ddc/scripts/fwimage.py) + arcade.py's tag
VCP_APP = 0xEB                          # AwtoApps.h: values AWTO_APPS_VCP_BASE + index start an app, 0 stops
VCP_BASE = 0x20
ROW_DISP_ROTATE = 32                    # registry row id of disp_rotate
ROTATE_SETTLE_S = 6.0                   # fw time for the display re-set after Rotate changes (as ddc asteroids_sim)
SETTLE_S = 0.5                          # fw time for a main pass to serve the start request + the init draw
MENU_SETTLE_S = 0.3                     # fw time for the MENU key inject to reach the key hook
HB_MASK = 0xFFFF                        # heartbeat is a 16 bit counter
VCP_MUTE = 0x8D                         # MCCS audio mute: 1 = muted, 2 = unmuted
MUTE_ON, MUTE_OFF = 1, 2
REQ_STOP = 0xFF                         # AwtoApps.h AWTO_APPS_REQ_STOP (debug byte g_ucAwtoAppReq)
BASE_S = 1.0                            # no-app window for the baseline cycles / pass
PROGRESS = {                            # app name -> (map symbol, bytes, what it counts)
    "pacman": ("g_usAwtoPcStep", 2, "game sub-steps"),
    "asteroids": ("g_usAwtoAstStep", 2, "game steps"),
    "scope2": ("g_usAwtoS2Frame", 2, "frames"),
}
COLS = ["game", "idx", "sound", "seconds", "progress", "progress_unit", "passes", "cycles_pass",
        "tone_s", "pitch_events", "osd_cells", "osd_uniq_ids", "menu_stops_it", "scaleup_off_after_stop", "vcp0_stops", "debug_byte_start_stop"]


def say(s: str) -> None:
    _log_line(s, LOG)


def apps(stem: Path) -> list[tuple[int, str]]:
    out = []
    for ln in stem.with_name(stem.name + ".apps.tsv").read_text().splitlines():
        f = ln.split("\t")
        out.append((int(f[0]), f[1]))
    return out


class Meter:
    def __init__(self, sess):
        self.sess, self.m = sess, sess.bus.m

    def mark(self):
        return int(self.m.p.cycles), self.sess.bus.diag()["hb"]

    def delta(self, a, b):
        passes = (b[1] - a[1]) & HB_MASK
        return passes, (b[0] - a[0]) / passes if passes else 0.0


def run_one(a, sess, ddc, tap, meter, idx, name, muted, base, run_addr):
    m, wait = sess.bus.m, sess.bus.wait
    sym, nbytes, unit = PROGRESS[name]
    pa = m.addr(sym)
    prog = lambda: int.from_bytes(m.rd(pa, nbytes), "big")              # noqa: E731  big-endian image
    tag = f"{name}{'_rot' if a.rotate else ''}{'_mute' if muted else ''}"
    tap.events.clear()
    tap.armed = True
    ddc.set(VCP_APP, VCP_BASE + idx)
    wait(SETTLE_S)
    running = m.rd(run_addr)[0] == idx + 1
    p0, c0, t_start = prog(), meter.mark(), sess.bus.now()
    wait(a.seconds)
    c1, p1, t_end = meter.mark(), prog(), sess.bus.now()
    passes, cyc = meter.delta(c0, c1)
    st = sess.snap()
    png = a.out / f"{tag}.png"
    R.render_snap(st, "black", 2).save(png)
    info = R.M.summary(st)
    (a.out / f"{tag}.events.tsv").write_text("".join("\t".join(map(str, e)) + "\n" for e in tap.events))
    wav = A.write_wav(a.out / f"{tag}.wav", tap.events, t_start, t_end)
    pitch = sum(1 for e in tap.events if e[1] == "reg" and e[2] == A.IDX_SCAPR)
    sess.act("exit")                                                    # MENU: the apps' quit key (arcade.h ARC_KEY_QUIT)
    wait(MENU_SETTLE_S)
    stopped = m.rd(run_addr)[0] == 0
    tap.armed = False
    after = R.M.summary(sess.snap())
    osd_off = after.get("su_on", 1) == 0                                # the stop path closed the screen: scale-up off (AwtoAppScreenEnd)
    ddc.set(VCP_APP, VCP_BASE + idx)
    wait(SETTLE_S)
    ddc.set(VCP_APP, 0)
    wait(SETTLE_S)
    vcp0 = m.rd(run_addr)[0] == 0
    req = sess.bus.m.addr("g_ucAwtoAppReq")
    m.wr(req, bytes([idx + 1]))
    wait(SETTLE_S)
    dbg_on = m.rd(run_addr)[0] == idx + 1
    m.wr(req, bytes([REQ_STOP]))
    wait(SETTLE_S)
    dbg = dbg_on and m.rd(run_addr)[0] == 0
    row = [name, idx, "off" if muted else "on", f"{t_end - t_start:.1f}", (p1 - p0) & 0xFFFF, unit, passes, f"{cyc:.0f}",
           f"{wav['tone_s']:.2f}", pitch, f"{info['cols']}x{info['rows']}", info.get("uniq_ids", ""), int(stopped), int(osd_off), int(vcp0), int(dbg)]
    say(f"{name} sound {row[2]}: started {int(running)}, {row[4]} {unit} in {row[3]} s fw, {passes} passes, {row[7]} cycles/pass, "
        f"tone {row[8]} s / {row[9]} pitch writes, OSD {row[10]} {row[11]} ids, MENU stops it {int(stopped)}, scale-up off after stop {int(osd_off)}, VCP 0 stops {int(vcp0)}, debug byte start/stop {int(dbg)} -> {png}")
    wait(SETTLE_S)
    return row, running and p1 != p0 and stopped and vcp0 and dbg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bin", type=Path, nargs="?", default=DDC_FW / (STEM + ".bin"))
    ap.add_argument("map", type=Path, nargs="?")
    ap.add_argument("--game", default="")
    ap.add_argument("--seconds", type=float, default=8.0, help="fw time each app runs")
    ap.add_argument("--out", type=Path, default=ROOT / "tmp/arcade_sim")
    ap.add_argument("--rotate", action="store_true", help="display Rotate 180 first (docs/osd/rotation.md)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    mapp = a.map or a.bin.with_suffix(".map")
    games = [(i, n) for i, n in apps(a.bin.with_suffix("")) if not a.game or n == a.game]
    if not games:
        say(f"no app {a.game!r} in {a.bin.with_suffix('.apps.tsv')}")
        return 1
    eng = D.DdcEngine()
    tap = A.AudioTap(lambda: sess.bus.now() if tap.armed else 0.0)
    tap.armed = False
    sess = R.Session(a.bin, mapp, "1080p60", devs=[eng, tap])
    sess.boot()
    ddc = D.Mccs(sess.bus, eng)
    wait, m = sess.bus.wait, sess.bus.m
    if a.rotate:
        ddc.set(0xE0, ROW_DISP_ROTATE)
        ddc.set(0xE1, 1)
        wait(ROTATE_SETTLE_S)
    meter = Meter(sess)
    run_addr = m.addr("g_ucAwtoAppRun")
    t0 = meter.mark()
    wait(BASE_S)
    passes, base = meter.delta(t0, meter.mark())
    say(f"baseline (no app): {passes} passes in {BASE_S} s fw, {base:.0f} cycles/pass")
    rows, fails = [], 0
    for idx, name in games:
        for muted in (0, 1):
            ddc.set(VCP_MUTE, MUTE_ON if muted else MUTE_OFF)
            wait(SETTLE_S)
            row, ok = run_one(a, sess, ddc, tap, meter, idx, name, muted, base, run_addr)
            rows.append(row)
            fails += 0 if ok else 1
    (a.out / "arcade_sim.tsv").write_text("\t".join(COLS) + "\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows))
    sess.bus.close()
    say(f"arcade_sim: {len(rows)} app(s), {fails} did not start / progress / stop -> {a.out / 'arcade_sim.tsv'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
