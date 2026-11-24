"""Native pistol, combat timers, death, corpse collision and HUD integration."""
import json,os,struct
from pathlib import Path
import pytest
from PIL import Image
from test_doom_platform import toolchain
import doom_renderer as R,doom_assets as A,doom_play as P

@pytest.fixture(scope='module')
def combat_renderer(tmp_path_factory):
    wad=os.environ.get('AWTO_DOOM_WAD')
    if not wad:pytest.skip('set AWTO_DOOM_WAD')
    out=tmp_path_factory.mktemp('combat-renderer')
    R.build(*toolchain(True),out,width=30,height=64)
    return Path(wad),out

def fixture_actors(monkeypatch,rows,*,frame=0,tics=0,awake=0):
    original=A.pack
    def load(wad_path,image,memory,out,**kw):
        boot,assets=original(wad_path,image,memory,out,**kw)
        struct.pack_into('<H',memory,0xD0010,len(rows))
        for i,row in enumerate(rows):
            x,y,health=row[:3];kind=row[3] if len(row)>3 else 0
            struct.pack_into('<hhHHiHBBhH',memory,0xD0020+i*20,x,y,32768,kind,0,tics,frame,awake,0,health)
        assets['monsters']['count']=len(rows)
        return boot,assets
    monkeypatch.setattr(A,'pack',load)

POSE=dict(x=2184*65536,y=-2392*65536,angle=0,viewz=57*65536)

def test_nearest_hit_pain_death_and_corpses_stop_blocking(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2240,-2392,20),(2272,-2392,60)])
    commands=[dict(buttons=2)]*22+[dict(forward=4)]*35
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    f=r['frames'];assert f[0]['combat']['target']==1
    assert f[0]['actors']['things'][0]['health']==0
    assert f[0]['actors']['things'][1]['health']==60
    assert any(x['actors']['things'][1]['frame']==6 for x in f)
    assert f[-1]['combat']['hits']==4 and f[-1]['combat']['kills']==2
    for i in (0,1):
        assert f[-1]['actors']['things'][i]['health']==0
        assert f[-1]['actors']['things'][i]['frame']==11
    assert f[-1]['motion']['x']>2240*65536  # player crossed the dead body's box
    assert len({(x['actors']['things'][0]['x'],x['actors']['things'][0]['y']) for x in f})==1
    assert r['stack_wraps']==0


def test_wall_occlusion_and_missed_shots_consume_ammo(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(3440,-3472,20)])
    pose=dict(x=3296*65536,y=-3472*65536,angle=0,viewz=41*65536)
    r,_=R.simulate(wad,out,initial_pose=pose,commands=[dict(buttons=2)],frames=1,latency=64)
    assert r['frames'][0]['combat']['shots']==1
    assert r['frames'][0]['combat']['ammo']==49
    assert r['frames'][0]['combat']['hits']==0
    assert r['frames'][0]['actors']['things'][0]['health']==20


def test_cadence_empty_ammo_and_release_do_not_create_extra_shots(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[])
    commands=[dict(buttons=2)]*260+[{}]*10
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    for f in r['frames'][:260]:
        expected=min(50,(f['actors']['stats']['ticks']-1)//7+1)
        assert f['combat']['shots']==expected
        assert f['combat']['ammo']==50-expected
    assert r['frames'][-1]['combat']['shots']==50
    assert r['frames'][-1]['combat']['ammo']==0
    assert r['frames'][-1]['combat']['hits']==0


def test_contact_attacks_health_death_and_frozen_input(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2216,-2408,20),(2216,-2376,20)])
    commands=[{}]*240+[dict(forward=8,buttons=2)]*10
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    states=r['frames'];dead=next(i for i,f in enumerate(states) if f['combat']['dead'])
    assert any(f['combat']['hurt'] for f in states[:dead])
    assert states[dead]['combat']['health']==0
    assert states[dead]['combat']['damage']==100
    assert states[dead]['combat']['attacks']>=10
    final=states[-1]
    assert final['motion']['x']==states[dead]['motion']['x']
    assert final['motion']['ticks']==states[dead]['motion']['ticks']
    assert final['combat']['shots']==0 and final['combat']['ammo']==50
    assert r['stack_wraps']==0


def test_native_hud_digits_crosshair_and_original_weapon_pixels(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[])
    R.simulate(wad,out,initial_pose=POSE,hud=False,latency=64)
    background=Image.open(out/'e1m1-native.png').copy()
    R.simulate(wad,out,initial_pose=POSE,hud=True,latency=64)
    actual=Image.open(out/'e1m1-native.png')
    w=A.Wad(wad);palette=w['PLAYPAL'][:768]
    rgb=lambda c:tuple(palette[c*3:c*3+3])
    assert actual.getpixel((15,32))==rgb(4)
    # Independent post decoder and nearest-neighbour weapon sample oracle.
    raw=w['PISGA0'];width,height,*_=struct.unpack_from('<4h',raw)
    pixels={}
    for x in range(width):
        off=struct.unpack_from('<I',raw,8+x*4)[0]
        while raw[off]!=255:
            top,count=raw[off],raw[off+1]
            for y,c in enumerate(raw[off+3:off+3+count],top):pixels[x,y]=c
            off+=count+4
    for x in range(8):
        for y in range(21):
            source=pixels.get((x*width//8,y*height//21))
            pos=(11+x,34+y)
            assert actual.getpixel(pos)==(rgb(source) if source is not None else background.getpixel(pos))
    shapes={'0':['111','101','101','101','111'],'1':['010','110','010','010','111'],'5':['111','100','111','001','111']}
    shapes['1']=['010']*5
    for start,text in ((2,'100'),(17,'050')):
        for i,ch in enumerate(text):
            for y,row in enumerate(shapes[ch]):
                for x,b in enumerate(row):assert actual.getpixel((start+i*4+x,57+y))==rgb(4 if b=='1' else 0)


def test_quick_fire_and_use_taps_are_latched_independently():
    s=P.PlaySession(preview_hz=0)
    s.set_command(dict(buttons=2));s.set_command(dict(buttons=0))
    s.set_command(dict(buttons=1));s.set_command(dict(buttons=0))
    assert s.command(0)['buttons']==3
    assert s.command(1).get('buttons',0)==0


@pytest.mark.parametrize('kind,ranged',[(0,False),(1,True)])
def test_soldier_fires_at_range_while_imp_throws_fireball(combat_renderer,monkeypatch,kind,ranged):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,20,kind)])
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=[{}]*38,frames=38,latency=64,save_frames=False)
    f=r['frames']
    if ranged:
        assert r['assets']['monsters']['ranged_kinds']==2
        hit=next(i for i,s in enumerate(f) if s['combat']['damage'])
        attack=next(i for i,s in enumerate(f) if s['actors']['things'][0]['frame']==4)
        assert attack<hit
        assert f[hit]['combat']['health']==90
        assert f[hit]['actors']['things'][0]['x']-2184>48
        assert f[hit]['actors']['things'][0]['frame']==5
        assert f[-1]['combat']['attacks']==1  # recovery prevents immediate repeats
    else:
        assert f[-1]['projectiles']['stats']['spawned']==1
        assert f[-1]['combat']['attacks']==1
    assert r['stack_wraps']==r['ddr']['invalid']==r['ddr']['hazards']==0


@pytest.mark.parametrize('x,y,pose',[
    (3440,-3472,dict(x=3296*65536,y=-3472*65536,angle=0,viewz=41*65536)),
    (2800,-2392,POSE),
])
def test_soldier_rechecks_wall_sight_and_range_at_impact(combat_renderer,monkeypatch,x,y,pose):
    wad,out=combat_renderer
    # Start one tick before impact: no chase/wakeup can hide a bad hit check.
    fixture_actors(monkeypatch,[(x,y,20,1)],frame=4,tics=7,awake=1)
    r,_=R.simulate(wad,out,initial_pose=pose,commands=[{}],frames=1,latency=64)
    c=r['frames'][0]['combat']
    assert c['attacks']==1 and c['damage']==0 and c['health']==100


@pytest.mark.parametrize('health',[20,60])
def test_pain_or_death_interrupts_a_soldiers_pending_shot(combat_renderer,monkeypatch,health):
    wad,out=combat_renderer
    fixture_actors(monkeypatch,[(2272,-2392,health,1)],frame=4,tics=7,awake=1)
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=[dict(buttons=2)]+[{}]*15,frames=16,latency=64,save_frames=False)
    assert r['frames'][-1]['combat']['kills']==int(health==20)
    assert r['frames'][0]['actors']['things'][0]['frame']==(7 if health==20 else 6)
    assert all(s['combat']['attacks']==s['combat']['damage']==0 for s in r['frames'])


@pytest.mark.parametrize('types,expected',[( [3004],1),([9,3001,3004],5)])
def test_ranged_mask_follows_map_kind_order_and_older_images(combat_renderer,types,expected):
    import doom_sim as S
    wad,out=combat_renderer;image=bytearray(S.load_ihx(out/'doom_renderer.ihx'))
    things=b''.join(struct.pack('<hhHHH',2272,-2392,180,t,2) for t in types)
    for version,mask in ((4,expected),(3,0)):
        image[0xFFF4]=version;loaded={}
        def load(address,data,label):loaded[address]=bytes(data);return address
        assets=A.pack_monsters(A.Wad(wad),things,image,load)
        assert assets['types']==sorted(types)
        assert assets['ranged_kinds']==mask
        assert struct.unpack_from('<HH',loaded[0xD0010])==(len(types),mask)
