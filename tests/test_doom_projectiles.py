"""Native banked fireball motion, impacts, dodging and exact sine values."""
import json,struct
from pathlib import Path
import pytest
from test_doom_combat import combat_renderer,fixture_actors,POSE
from test_doom_platform import build_platform
import doom_renderer as R,doom_assets as A,doom_sim as S,fastmachine as F,ddr_sim as D

def test_all_native_trig_samples_are_exact(combat_renderer,tmp_path):
    wad,out=combat_renderer
    trig=tmp_path/'trig_source.c'
    trig.write_text((out/'trig.c').read_text().replace('#include "platform.h"','#include "'+str(R.ROOT/'fw/doom/platform.h')+'"'))
    build_platform(tmp_path,True,R.ROOT/'tests/doom_trig_fw.c',(trig,))
    c=F.Core(S.load_ihx(tmp_path/'platform.ihx'));c.set_dw(json.loads(F.MODEL_JSON.read_text()));c.reset();c.set_xpage_sfr(0x92);c.set_ddr(D.config(),latency_clk=64)
    table=next(t for t in json.loads((out/'tables.json').read_text()) if t['name']=='finesineTable_part_1')
    raw=bytes.fromhex(table['hex']);c.ddr_mem()[table['address']:table['address']+len(raw)]=raw
    values=struct.unpack('<2048H',raw)
    # Original table truncates positive samples; compare against its exact raw
    # half-step values and quadrant symmetry, not a new floating-point table.
    expected=list(values)+list(reversed(values))+[-v for v in values]+[-v for v in reversed(values)]
    try:
        for _ in range(20):
            c.run(10000)
            if c.xram[0xF600]==0xA5:break
        for i in range(8192):
            c.xram[0xF620:0xF622]=i.to_bytes(2,'little');c.xram[0xF62C]=1
            for _ in range(20):
                c.run(2000)
                if not c.xram[0xF62C]:break
            assert not c.xram[0xF62C]
            assert struct.unpack('<ii',c.xram[0xF624:0xF62C])==(expected[i],expected[(i+2048)&8191])
        assert not c.p.sp_wrap
    finally:c.free()

def test_native_banks_fireball_hit_and_source_death(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,20)])  # kind zero is imp in E1M1
    commands=[{}]*29+[dict(buttons=2)]*25
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    assert r['banking']['banks']==3 and r['bank_switches']>100 and r['bank_switches']%2==0
    assert r['frames'][-1]['projectiles']['stats']['spawned']>=1
    assert r['frames'][-1]['projectiles']['stats']['hits']>=1
    assert r['frames'][-1]['combat']['damage']>=10
    assert r['frames'][-1]['combat']['kills']==1
    assert any(s['active'] and s['phase']==1 for f in r['frames'] for s in f['projectiles']['slots'])
    assert any(s['active'] and s['frame'] in (2,3,4) for f in r['frames'] for s in f['projectiles']['slots'])
    assert any(f['actors']['things'][0]['health']==0 and any(s['active'] and s['phase']==1 for s in f['projectiles']['slots']) for f in r['frames'])
    assert r['stack_wraps']==0

def test_fireball_can_be_dodged_and_hits_world(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,20)])
    original=A.pack
    def wall(*args,**kw):
        boot,assets=original(*args,**kw)
        # Initial collision fixture: a wall beyond the stationary player. It
        # cannot block launch sight, but must catch the ball after the dodge.
        struct.pack_into('<6h4B',args[2],0x80010,2140,-2460,2140,-2320,0,0,1,0,255,0)
        return boot,assets
    monkeypatch.setattr(A,'pack',wall)
    commands=[{}]*29+[dict(strafe=8,buttons=2)]*16+[{}]*20
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    p=r['frames'][-1]['projectiles']['stats']
    assert p['spawned']>0 and p['walls']>0
    assert p['hits']==0
    assert r['frames'][-1]['combat']['health']==100
    assert all(f['projectiles']['verified'] for f in r['frames'])

def test_soldier_ranged_shot_and_wall_occlusion(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,20)])
    original=A.pack
    def soldier(*args,**kw):
        boot,assets=original(*args,**kw);args[2][0xD3010:0xD3012]=b'\0\0';return boot,assets
    monkeypatch.setattr(A,'pack',soldier)
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=[{}]*35,frames=35,latency=64,save_frames=False)
    assert r['frames'][-1]['combat']['damage']==10
    assert r['frames'][-1]['projectiles']['stats']['spawned']==0


def test_projectile_pool_saturation_preserves_existing_slots(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,60)]*9)
    original=A.pack
    def windups(*args,**kw):
        boot,assets=original(*args,**kw)
        # Native capacity fixture: nine simultaneous completed attack windups.
        for i in range(9):struct.pack_into('<HBB',args[2],0xD0020+i*20+12,7,4,1)
        return boot,assets
    monkeypatch.setattr(A,'pack',windups)
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=[{}],latency=64)
    p=r['frames'][0]['projectiles']
    assert p['stats']['spawned']==8 and p['stats']['dropped']==1
    assert sum(s['active'] for s in p['slots'])==8
    assert [s['owner'] for s in p['slots']]==list(range(8))


def test_wall_blocks_an_already_wound_up_soldier(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(3440,-3472,20)])
    original=A.pack
    def windup(*args,**kw):
        boot,assets=original(*args,**kw)
        args[2][0xD3010:0xD3012]=b'\0\0'
        struct.pack_into('<HBB',args[2],0xD0020+12,7,4,1)
        return boot,assets
    monkeypatch.setattr(A,'pack',windup)
    pose=dict(x=3296*65536,y=-3472*65536,angle=0,viewz=41*65536)
    r,_=R.simulate(wad,out,initial_pose=pose,commands=[{}],latency=64)
    assert r['frames'][0]['combat']['attacks']==1
    assert r['frames'][0]['combat']['health']==100
    assert r['frames'][0]['projectiles']['stats']['spawned']==0
