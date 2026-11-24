#!/usr/bin/env python3
"""Run a scripted Doom demo on the fast DW8051 core (mcs51_core.c) and encode a model-paced mp4.

Frames are CPU-written (native firmware); pacing = per-frame CPU-model time (assumed 350.791 MHz), not measured hardware.
Logs: ./tmp/logs/doom_fastsim_video.log. Raw frames: ./tmp/scratch/ (not committed).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.append(os.environ.get("AWTO_DDC_SCRIPTS", "/mnt/2tb/git/awto-ddc/scripts"))   # sdcc_overlay etc. live in awto-ddc
import doom_renderer as R   # noqa: E402

FFMPEG_STALL_S = 120   # x264 of <= ~500 small frames: expected < 10 s; expiry = ffmpeg hung


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--map", default="E1M1")
    p.add_argument("--demo", type=Path, default=ROOT / "examples/doom-fireballs-demo.json")
    p.add_argument("--pose", type=Path, default=ROOT / "examples/doom-fireballs-pose.json")
    p.add_argument("--out", type=Path, help="build dir (default translated/native/<map>)")
    p.add_argument("--date", required=True, help="YYYYMMDD for the file name")
    p.add_argument("--scale", type=int, default=8)
    a = p.parse_args()
    out = a.out or ROOT / "translated/native" / a.map
    commands = json.loads(a.demo.read_text())
    pose = json.loads(a.pose.read_text()) if a.pose else None
    frames_dir = ROOT / "tmp/scratch" / f"fastsim-{a.map}"
    shutil.rmtree(frames_dir, ignore_errors=True)
    frames_dir.mkdir(parents=True)
    records = []

    def on_frame(image, record, index):
        from PIL import Image
        image.resize((image.width * a.scale, image.height * a.scale), Image.Resampling.NEAREST).save(frames_dir / f"f{index:04d}.png")
        records.append(dict(model_ms=record["model_ms"], combat=record.get("combat")))
        return True

    t0 = time.monotonic()
    R.simulate(None, out, mapname=a.map, packed=out, frames=len(commands), commands=commands, initial_pose=pose,
               on_frame=on_frame, save_frames=False, latency=64)
    wall = time.monotonic() - t0
    model_s = sum(r["model_ms"] for r in records) / 1000
    # model-paced: each frame shown for its CPU-model duration (ffconcat durations)
    concat = frames_dir / "model.ffconcat"
    lines = ["ffconcat version 1.0"]
    for i, r in enumerate(records):
        lines += [f"file f{i:04d}.png", f"duration {r['model_ms'] / 1000:.6f}"]
    lines.append(f"file f{len(records) - 1:04d}.png")
    concat.write_text("\n".join(lines) + "\n")
    mp4 = ROOT / "previews" / f"doom-fastsim-{a.map.lower()}-{a.date}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", str(concat), "-vf", "fps=25,format=yuv420p",
                    "-c:v", "libx264", "-crf", "20", str(mp4)], check=True, stdin=subprocess.DEVNULL, timeout=FFMPEG_STALL_S)
    worst = max(r["model_ms"] for r in records)
    summary = dict(map=a.map, demo=str(a.demo.relative_to(ROOT)), frames=len(records), wall_s=round(wall, 2),
                   wall_ms_per_frame=round(wall * 1000 / len(records), 1), model_movie_s=round(model_s, 2),
                   model_ms_worst=round(worst, 2), model_ms_mean=round(model_s * 1000 / len(records), 2),
                   speed_vs_model=round(model_s / wall, 3), final_combat=records[-1]["combat"], mp4=str(mp4.relative_to(ROOT)),
                   mp4_bytes=mp4.stat().st_size)
    (ROOT / "previews" / f"doom-fastsim-{a.map.lower()}-{a.date}.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
