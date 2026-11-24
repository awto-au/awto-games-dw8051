"""Real 8051 actor collision/sight queries and moving-monster integration."""
import json,os,struct
from pathlib import Path
import pytest
from test_doom_motion import motion_image,Player
from test_doom_sprites import sprite_renderer
import doom_renderer as R

def query(p,op,*args):
    p.c.xram[0xF650:0xF65A]=struct.pack('<5h',*(list(args)+[0]*(5-len(args))))
    p.c.xram[0xF620]=op
    for _ in range(100):
        p.c.run(10000)
        if not p.c.xram[0xF620]:break
    else:pytest.fail('native actor query timed out')
    assert not p.c.p.sp_wrap
    return p.c.xram[0xF65A]

@pytest.mark.parametrize('floor,ceiling,solid,accept',[(0,128,1,False),(0,128,0,True),(24,128,0,True),(25,128,0,False),(0,55,0,False),(-24,128,0,True),(-25,128,0,False)])
def test_actor_geometry_and_player_state_isolation(motion_image,floor,ceiling,solid,accept):
    p=Player(motion_image,[(64,-128,64,128,max(0,floor),min(128,ceiling),solid)],floor_b=floor,ceiling_b=ceiling)
    try:
        before=bytes(p.c.xram[0xF6A0:0xF6B8])
        assert bool(query(p,2,80 if floor<0 else 64,0,0))==accept
        assert bytes(p.c.xram[0xF6A0:0xF6B8])==before
        if accept:assert struct.unpack('<h',p.c.xram[0xF65C:0xF65E])[0]==floor
        # Player collision still works after a differently positioned actor probe.
        r=p.frame(forward=8)
        assert r['x']==8*65536 and r['floor']==0
    finally:p.free()

@pytest.mark.parametrize('floor,ceiling,solid,visible',[(0,128,1,False),(0,128,0,True),(0,0,0,False),(0,40,0,False),(0,42,0,True),(48,128,0,False)])
def test_native_sight_uses_live_portal_heights(motion_image,floor,ceiling,solid,visible):
    p=Player(motion_image,[(64,-128,64,128,max(0,floor),min(128,ceiling),solid)],floor_b=floor,ceiling_b=ceiling)
    try:
        assert bool(query(p,3,0,0,128,0,41))==visible
        assert bool(query(p,3,128,0,0,0,41))==visible
        assert query(p,3,0,200,128,200,41)==1  # misses the segment entirely
    finally:p.free()


def test_player_body_hook_and_actor_door_obstruction(motion_image):
    from test_doom_doors import door_player,door
    p=Player(motion_image,[(500,-128,500,128,0,0,1)])
    try:
        query(p,4)
        for _ in range(20):r=p.frame(forward=8)
        assert r['x']==56*65536
    finally:p.free()
    p=door_player(motion_image)
    try:
        query(p,5)
        p.frame(buttons=1)
        for _ in range(210):p.frame()
        r=door(p)
        assert r['reopens']>0 and r['states'][0]['height']>=56
    finally:p.free()


def test_original_monsters_wake_chase_animate_and_block_player(sprite_renderer):
    wad,out=sprite_renderer
    pose=dict(x=2128*65536,y=-2392*65536,angle=0,viewz=17*65536)
    commands=[{}]*100+[dict(forward=8)]*30
    r,_=R.simulate(wad,out,initial_pose=pose,commands=commands,frames=len(commands),latency=64)
    first,last=r['frames'][0],r['frames'][-1]
    assert first['actors']['stats']['awake']==2
    assert last['actors']['stats']['moves']>0
    assert last['actors']['stats']['blocked']>0
    for i in (4,5):
        assert last['actors']['things'][i]['x']<first['actors']['things'][i]['x']-40
        assert {f['actors']['things'][i]['frame'] for f in r['frames']}>={0,1,2,3}
    assert last['motion']['x']<2250*65536
    assert any(f['motion']['blocked'] for f in r['frames'][100:])
    assert all(f['actors']['verified'] and f['world_verified'] and f['motion_verified'] for f in r['frames'])
    assert r['stack_wraps']==0
    # The four distant monsters remain at their original map coordinates.
    assert [t['awake'] for t in last['actors']['things'][:4]]==[0]*4


def test_real_actor_reopens_a_closing_door(sprite_renderer,monkeypatch):
    import doom_assets as A
    wad,out=sprite_renderer
    original=A.pack
    selected={}
    def initial_fixture(wad_path,image,memory,out,**kw):
        boot,assets=original(wad_path,image,memory,out,**kw)
        # Initial geometry only: one real sprite in an already open E1M1 door.
        door=next(d for d in assets['doors'] if d['bbox'][0]<=1544<=d['bbox'][1] and d['bbox'][2]<=-2496<=d['bbox'][3])
        selected.update(door)
        struct.pack_into('<H',memory,0xD0010,1)
        struct.pack_into('<hhHHiHBBhH',memory,0xD0020,1544,-2496,32768,0,0,0,0,0,0,0)
        assets['monsters']['count']=1
        schema=assets['schema'];secsz,fo,co=schema[:3]
        struct.pack_into('<i',memory,0x20010+door['sector']*secsz+co,door['top']*65536)
        # Update the static initial profiles to match this initial ceiling.
        for i in range(assets['lines']):
            p=0x80010+i*16;front,back=memory[p+13],memory[p+14]
            if back==255 or memory[p+12]&1:continue
            ceilings=[struct.unpack_from('<i',memory,0x20010+s*secsz+co)[0]>>16 for s in (front,back)]
            struct.pack_into('<h',memory,p+10,min(ceilings))
        return boot,assets
    monkeypatch.setattr(A,'pack',initial_fixture)
    pose=dict(x=1488*65536,y=-2496*65536,angle=0,viewz=41*65536)
    commands=[dict(buttons=1)]+[{}]*139
    r,_=R.simulate(wad,out,initial_pose=pose,commands=commands,frames=len(commands),latency=64)
    assert r['frames'][-1]['doors']['reopens']>0
    assert all(f['motion']['x']==1488*65536 for f in r['frames'])
    assert all(f['actors']['verified'] and f['world_verified'] for f in r['frames'])
    actor=r['frames'][-1]['actors']['things'][0]
    assert actor['x']+16>=selected['bbox'][0]  # actor remains in door's box
    assert 1488+16<selected['bbox'][0]  # player cannot be the obstruction
    assert r['stack_wraps']==0
