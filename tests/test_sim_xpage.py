"""DW8051 direct-bus page selection, using actual MOVX @Ri opcodes."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fastmachine as F

@pytest.mark.parametrize('register',[None,0x92])
def test_movx_ri_page_selection_reset_and_snapshot(register):
    # R0/R1 read one page and write both returned bytes elsewhere in that page.
    program=bytes.fromhex('78 10 79 11 e2 f5 30 e3 f5 31 78 12 79 13 e5 30 f2 e5 31 f3')
    c=F.Core(program+bytes(65536-len(program)))
    try:
        if register is not None: c.set_xpage_sfr(register)
        def run():
            c.p.pc=0
            c.sfr_write(0xA0,0xD8)
            c.sfr_write(0x92,0xD9)
            assert c.run(12)==F.R_DONE
        c.xram[0xD810:0xD812]=b'\x12\x34'
        c.xram[0xD910:0xD912]=b'\x56\x78'
        snap=c.snap()
        for method in ('initial','restore','reset'):
            if method=='restore':
                c.set_xpage_sfr(0x92 if register is None else 0xA0)
                c.restore(snap)
            elif method=='reset': c.reset()
            run()
            page=0xD800 if register is None else 0xD900
            want=b'\x12\x34' if register is None else b'\x56\x78'
            assert bytes(c.xram[page+0x12:page+0x14])==want
            assert bytes(c.iram[0x30:0x32])==want
    finally: c.free()

@pytest.mark.parametrize('address',[-1,0,0x7f,0x100,65535])
def test_page_selector_rejects_non_sfr(address):
    c=F.Core(bytes(65536))
    try:
        with pytest.raises(ValueError): c.set_xpage_sfr(address)
    finally: c.free()
