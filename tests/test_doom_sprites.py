"""Native sprite pixels checked against an independent fixed-point oracle."""
import json,os,struct
from pathlib import Path
import pytest
from PIL import Image
from test_doom_platform import toolchain
import doom_renderer as R
import doom_assets as A

@pytest.fixture(scope='module')
def sprite_renderer(tmp_path_factory):
    wad=os.environ.get('AWTO_DOOM_WAD')
    if not wad:pytest.skip('set AWTO_DOOM_WAD')
    out=tmp_path_factory.mktemp('sprite-renderer')
    R.build(*toolchain(True),out,width=60,height=128)
    return Path(wad),out


def test_original_map_filter_and_wall_occlusion(sprite_renderer):
    wad,out=sprite_renderer
    # This actual E1M1 imp is behind a wall from the selected camera position.
    pose=dict(x=3296*65536,y=-3472*65536,angle=0,viewz=41*65536)
    r,_=R.simulate(wad,out,initial_pose=pose,latency=64)
    assert r['assets']['monsters']['count']==6
    assert r['frames'][0]['sprites']['projected']>0
    assert r['frames'][0]['sprites']['pixels']==0
    # Two original map things in front of the blue wall, with real transparency.
    pose=dict(x=2184*65536,y=-2392*65536,angle=0,viewz=41*65536)
    r,_=R.simulate(wad,out,initial_pose=pose,latency=64,frames=8,yaw_step=45)
    assert r['frames'][0]['sprites']['pixels']>500
    assert any(f['sprites']['pixels']==0 for f in r['frames'])
    for i in (1,4,7):
        pose['angle']=i*(1<<29)
        single,_=R.simulate(wad,out,initial_pose=pose,latency=64)
        assert Image.open(out/f'frame-{i:03d}.png').tobytes()==Image.open(out/'e1m1-native.png').tobytes()
    assert r['stack_wraps']==0


def test_native_projection_transparent_holes_and_palette(sprite_renderer,monkeypatch):
    wad,out=sprite_renderer
    pose=dict(x=2184*65536,y=-2392*65536,angle=0,viewz=41*65536)
    def empty(wad,things,image,load):
        load(0xD0010,bytes(16),'empty test things')
        return dict(count=0)
    monkeypatch.setattr(A,'pack_monsters',empty)
    R.simulate(wad,out,initial_pose=pose,latency=64,hud=False)
    background=Image.open(out/'e1m1-native.png').copy()
    def fixture(wad,things,image,load):
        # One transparent, asymmetric patch in open space, palette index 176.
        load(0xD0010,struct.pack('<H14xhhHHi8x',1,2272,-2392,0,0,0),'test thing')
        raw=bytearray(16*256)
        for x in range(16):
            for y in range(32):raw[x*256+y*2:x*256+y*2+2]=bytes((176,int((x+y)%3!=0)))
        load(0x400010,raw,'test transparent patch')
        load(0xE0010,struct.pack('<4hIB3x',16,32,8,32,0x400010,0)*96,'test rotations')
        return dict(count=1)
    monkeypatch.setattr(A,'pack_monsters',fixture)
    r,_=R.simulate(wad,out,initial_pose=pose,latency=64,drop_every=7,hud=False)
    actual=Image.open(out/'e1m1-native.png')
    expected=background.copy();pixels=0
    # Independent host oracle evaluates the supplied fixture only. It never
    # supplies rendered pixels, screen positions or visibility to the CPU.
    # Doom's half-step angle table gives sin(0)=25, cos(0)=65535.
    # Its integer map-depth divisor consequently truncates 87.998... to 87.
    xs=30*65536//87;ys=128*65536//87
    left=30*65536+(((88*25-8*65536)*xs)>>16)
    top=64*65536-15*ys  # actor platform floor 24, camera eye 41
    sxstep=(1<<32)//xs;systep=(1<<32)//ys
    palette=A.Wad(wad)['PLAYPAL'][:768]
    for x in range(60):
        for y in range(128):
            if x<left//65536 or y<top//65536:continue
            sx=(((x*65536-left)*sxstep)>>16)>>16
            sy=(((y*65536-top)*systep)>>16)>>16
            if 0<=sx<16 and 0<=sy<32 and (sx+sy)%3:
                expected.putpixel((x,y),tuple(palette[176*3:176*3+3]));pixels+=1
    assert actual.tobytes()==expected.tobytes()
    assert r['frames'][0]['sprites']['pixels']==pixels
    assert r['ddr']['dropped']>0 and r['stack_wraps']==0
