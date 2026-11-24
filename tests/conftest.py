"""Games tests import awto-ddc helpers (_log, _repo, osd_render, ddc_sim, ...): scripts/ of $AWTO_DDC_SCRIPTS goes on sys.path (docs/games/README.md)."""
import os
import sys
from pathlib import Path

for p in (Path(__file__).resolve().parents[1] / "scripts", Path(os.environ.get("AWTO_DDC_SCRIPTS", "/mnt/2tb/git/awto-ddc/scripts"))):
    if str(p) not in sys.path:
        sys.path.append(str(p))
os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [os.environ.get("PYTHONPATH", ""), str(p)]))   # scripts run as subprocesses
