"""The generated assembly stays reproducible; optional real DW8051 execution."""
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_generated_assembly_is_current():
    import doom_math_gen
    assert (ROOT / "fw/doom/fixed_math.asm").read_text() == "\n".join(doom_math_gen.out)


def test_arithmetic_on_dw8051(tmp_path):
    import doom_sim
    sdcc_dir = os.environ.get("AWTO_SDCC_BIN")
    sdcc = Path(sdcc_dir) / "sdcc" if sdcc_dir else shutil.which("sdcc")
    if not sdcc:
        pytest.skip("SDCC assembler/linker unavailable; set AWTO_SDCC_BIN")
    sdcc = Path(sdcc)
    # Only the assembler/linker is needed for the arithmetic image.
    doom_sim.command([sdcc.parent / "sdas8051", "-losg", tmp_path / "fixed_math.rel", ROOT / "fw/doom/fixed_math.asm"])
    doom_sim.command([sdcc.parent / "sdld", "-n", "-i", "-m", "-w", "-b", "CSEG=0x0100", "-b", "DSEG=0x30",
                      tmp_path / "fixed_math", tmp_path / "fixed_math.rel"])
    result = doom_sim.math_check(tmp_path, 1000)
    assert all(x["failures"] == 0 for x in result.values())
