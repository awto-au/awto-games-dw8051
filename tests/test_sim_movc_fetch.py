"""MOVC data fetches share the configured flash cache with instruction fetch."""
import json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fastmachine as F

@pytest.mark.parametrize('op',[0x83,0x93])
def test_movc_flash_data_cold_and_warm(op):
    model=json.loads(F.MODEL_JSON.read_text())
    code=bytearray(65536)
    if op==0x93:
        code[:6]=bytes.fromhex('90 01 00 74 03 93');pc,setup,address=5,2,0x103
    else:
        code[:3]=bytes.fromhex('74 40 83');pc,setup,address=2,1,0x43
    code[address]=0x77
    c=F.Core(bytes(code))
    try:
        c.set_dw(model);c.set_fetch(model);c.reset();c.xram[0xFDA0]=1
        c.L.core_set_fetch_ratio(c.h,3*256)
        c.run(setup)
        for cold in (True,False):
            c.p.pc=pc;c.sfr_write(0xE0,3 if op==0x93 else 0x40)
            before_clk,before_miss=c.p.clk,c.p.fm_miss
            assert c.run(1)==F.R_DONE
            assert c.regs()['acc']==0x77
            fill=model['flash_fetch']['fill_flash_clk']*3-model['clk_per_cycle']
            assert c.p.clk-before_clk==model['cycles'][op]*model['clk_per_cycle']+(fill if cold else 0)
            assert c.p.fm_miss-before_miss==(1 if cold else 0)
    finally:c.free()
