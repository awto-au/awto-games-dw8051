"""Repo root for scripts (same API as awto-ddc `_repo.py`; shadows it so ROOT is this repo). $AWTO_DOOM_REPO -> git toplevel -> file-relative."""
import os
import subprocess
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("AWTO_DOOM_REPO")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent
    if (here.parent / ".git").exists():
        return here.parent
    try:
        out = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2, check=False)   # local .git read ~1 ms; 2 s = cold exec
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return here.parent


ROOT = repo_root()
