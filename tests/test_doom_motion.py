"""Native controller/collision fixtures; no host moves the player."""
import json,struct,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_doom_platform import build_platform
import doom_sim as S,ddr_sim as D,fastmachine as F

STATE=struct.Struct('<iiIhhIBBBB')
KEYS=('x','y','angle','floor','ceiling','ticks','blocked','frame_ticks','fault','enabled')

@pytest.fixture(scope='module')
def motion_image(tmp_path_factory):
    out=tmp_path_factory.mktemp('native-motion')
    build_platform(out,True,ROOT/'tests/doom_motion_fw.c',(ROOT/'fw/doom/motion.c',ROOT/'fw/doom/doors.c'))
    return S.load_ihx(out/'platform.ihx')

class Player:
    def __init__(self,image,lines,*,floor_b=0,ceiling_b=128,x=0,y=0,angle=0,door=False,stay=False,keys=0,lock=0,switch=False,repeat=False,targets=1,switch_index=0,exit_kind=0,door_count=1,block_ids=None,manual_id=1):
        self.c=F.Core(image);self.c.set_dw(json.loads(F.MODEL_JSON.read_text()));self.c.reset();self.c.set_xpage_sfr(0x92)
        self.c.set_ddr(D.config(),latency_clk=64)
        for i,line in enumerate(lines):
            line=(*line[:6],line[6]|(2 if not(line[6]&1) and (floor_b!=0 or ceiling_b!=128) else 0))
            token=(((17+switch_index)|(128 if stay else 0)|(32 if repeat else 0)) if switch else ((129 if stay else 1)|(lock<<5))) if door and i==0 else 0
            self.c.ddr_mem()[0x80010+i*16:0x80020+i*16]=struct.pack('<6h4B',*line,0,1,token)
        # Every cell references the same bounded list, stressing duplicate IDs.
        words=[(-256)&65535,(-256)&65535,8,8]+[68]*64+[0,*(range(len(lines)) if block_ids is None else block_ids),65535]
        raw=struct.pack('<'+'H'*len(words),*words)
        self.c.ddr_mem()[0x90010:0x90010+len(raw)]=raw
        if door:
            header=struct.pack('<HHIII',door_count,1,0xA2010,0xA4010 if switch else 0,0xA6010)
            token=self.c.ddr_mem()[0x80010+15]
            action=((switch_index+1)|512|(int(repeat)<<10)|(int(stay)<<8)) if switch else (manual_id|(lock<<6)|(int(stay)<<8))
            self.c.ddr_mem()[0xA6010+token*2:0xA6012+token*2]=struct.pack('<H',action)
            definition=struct.pack('<HhhHH4h14x',1,0,124,0,1,64,80,-128,128)
            self.c.ddr_mem()[0xA0010:0xA0010+16+max(1,door_count)*32]=header+definition*max(1,door_count)
            self.c.ddr_mem()[0xA2010:0xA2012]=struct.pack('<H',0)
            if switch:
                table=struct.pack('<H14x',switch_index+1)
                for si in range(switch_index+1):
                    table+=struct.pack('<IHIhhH',targets,0,0xB0010+si*2,7,8,exit_kind)
                    self.c.ddr_mem()[0xB0010+si*2:0xB0012+si*2]=struct.pack('<h',7)
                self.c.ddr_mem()[0xA4010:0xA4010+len(table)]=table
        self.c.xram[0xF640:0xF64A]=struct.pack('<Hhhhh',len(lines),0,floor_b,128,ceiling_b)
        self.c.xram[0xF64A:0xF64C]=struct.pack('<H',keys)
        self.c.xram[0xF6A0:0xF6B8]=STATE.pack(x*65536,y*65536,angle,0,128,0,0,0,0,0)
        for _ in range(20):
            self.c.run(10000)
            if self.c.xram[0xF600]==0xA5:break
        else:pytest.fail('motion init did not return')
    def frame(self,forward=0,strafe=0,turn=0,enabled=1,buttons=0):
        self.c.xram[0xF610:0xF616]=struct.pack('<bbhBB',forward,strafe,turn,enabled,buttons)
        self.c.xram[0xF620]=1
        for _ in range(50):
            self.c.run(10000)
            if not self.c.xram[0xF620]:break
        else:pytest.fail(f'motion stalled at {self.c.p.pc:x}')
        assert self.c.p.sp_wrap==0
        assert self.c.ddr_stats()['invalid']==self.c.ddr_stats()['hazards']==0
        result=dict(zip(KEYS,STATE.unpack(self.c.xram[0xF6A0:0xF6B8])))
        assert result['fault']==0
        return result
    def free(self): self.c.free()

@pytest.mark.parametrize('floor_b,ceiling_b,solid,passable',[(0,128,1,False),(0,128,0,True),(24,128,0,True),(25,128,0,False),(0,55,0,False),(24,79,0,False),(24,80,0,True),(-64,128,0,True)])
def test_wall_steps_and_headroom(motion_image,floor_b,ceiling_b,solid,passable):
    p=Player(motion_image,[(64,-128,64,128,max(0,floor_b),min(128,ceiling_b),solid)],floor_b=floor_b,ceiling_b=ceiling_b)
    try:
        states=[p.frame(forward=8) for _ in range(12)]
        last=states[-1]
        if passable:
            assert last['x']>64*65536
            assert last['floor']==floor_b
        else:
            assert last['x']==48*65536
            assert any(s['blocked']&1 for s in states)
        assert last['ticks']==16
    finally:p.free()

def test_tick_clock_controls_and_wall_slide(motion_image):
    p=Player(motion_image,[(64,-128,64,256,0,0,1)])
    try:
        states=[p.frame(forward=127,strafe=4) for _ in range(10)]
        assert [s['frame_ticks'] for s in states]==[1,1,2,1,2]*2
        assert states[-1]['x']==48*65536
        assert states[-1]['y']==56*65536
        assert states[-1]['ticks']==14
        before=states[-1]
        off=p.frame(forward=8,enabled=0)
        assert off['x']==before['x'] and off['ticks']==before['ticks'] and off['frame_ticks']==0
    finally:p.free()

@pytest.mark.parametrize('angle,forward,strafe,xy',[(0,-4,0,(-4,0)),(0,0,-4,(0,-4)),(1<<30,4,0,(0,4)),(3<<30,4,0,(0,-4))])
def test_signed_and_rotated_commands(motion_image,angle,forward,strafe,xy):
    p=Player(motion_image,[(500,-128,500,128,0,0,1)],angle=angle)
    try:
        r=p.frame(forward=forward,strafe=strafe)
        assert (r['x'],r['y'])==(xy[0]*65536,xy[1]*65536)
    finally:p.free()

@pytest.mark.parametrize('turn,expected',[(32767,0x10000000),(-32768,0xF0000000)])
def test_native_turn_clamp(motion_image,turn,expected):
    p=Player(motion_image,[(500,-128,500,128,0,0,1)])
    try:assert p.frame(turn=turn)['angle']==expected
    finally:p.free()

def test_diagonal_wall_and_maximum_command_do_not_tunnel(motion_image):
    import doom_motion as M
    lines=[(-128,128,128,-128,0,0,1)]
    p=Player(motion_image,lines,x=-64,y=-64)
    try:
        results=[p.frame(forward=127,strafe=127) for _ in range(16)]
        for state in results:
            assert state['x']+state['y']<=-32*65536
            M.validate_pose(state,lines)
        assert any(s['blocked'] for s in results)
    finally:p.free()


def test_exact_geometric_oracle_touch_and_crossing():
    import doom_motion as M
    assert M.crosses_open_box(-10,0,10,0,-1,1,-1,1)
    assert M.crosses_open_box(10,0,-10,0,-1,1,-1,1)
    assert not M.crosses_open_box(-10,1,10,1,-1,1,-1,1)
    assert not M.crosses_open_box(1,1,2,2,-1,1,-1,1)


def test_native_wad_movement_and_independent_pose_render(tmp_path):
    import os
    import doom_renderer as R
    from test_doom_platform import toolchain
    wad=os.environ.get('AWTO_DOOM_WAD')
    if not wad:pytest.skip('set AWTO_DOOM_WAD')
    sdcc,linker,lib=toolchain(True)
    R.build(sdcc,linker,lib,tmp_path,width=30,height=48)
    commands=[dict(forward=8) for _ in range(20)]+[dict(forward=3,strafe=2,turn=256) for _ in range(20)]
    result,_=R.simulate(Path(wad),tmp_path,yaw=0,commands=commands,frames=len(commands),latency=64)
    assert all(f['motion_verified'] for f in result['frames'])
    assert any(f['motion']['blocked'] for f in result['frames'])
    assert result['frames'][-1]['motion']['ticks']==56
    from PIL import Image
    for i in (0,19,39):
        state=result['frames'][i]['motion']
        pose=dict(x=state['x'],y=state['y'],angle=state['angle'],viewz=(state['floor']+41)*65536)
        R.simulate(Path(wad),tmp_path,initial_pose=pose,latency=64)
        assert Image.open(tmp_path/f'frame-{i:03d}.png').tobytes()==Image.open(tmp_path/'e1m1-native.png').tobytes()
