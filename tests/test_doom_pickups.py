"""Original map pickups, exercised by native 8051 instructions and DDR sprites."""
import struct
import pytest
from test_doom_combat import combat_renderer,fixture_actors,POSE
import doom_renderer as R,doom_assets as A


def fixture_scene(monkeypatch,items,actors=(),**actor_state):
    fixture_actors(monkeypatch,list(actors),**actor_state)
    original=A.pack
    def load(*args,**kw):
        boot,assets=original(*args,**kw);memory=args[2]
        data=assets['monsters']['pickups'];data.update(count=len(items),things=[])
        struct.pack_into('<H',memory,0xD8010,len(items))
        for i,(x,y,typ) in enumerate(items):
            rule=A.PICKUPS[typ][1];kind=data['kinds'][typ]
            struct.pack_into('<hhHHiHBBhH',memory,0xD0020+(len(actors)+8+i)*20,x,y,0,kind,0,rule,0,0,0,1)
            data['things'].append(dict(x=x,y=y,type=typ,kind=kind,rule=rule))
        return boot,assets
    monkeypatch.setattr(A,'pack',load)


def run(scene,commands,**kw):
    wad,out=scene
    return R.simulate(wad,out,commands=commands,frames=len(commands),initial_pose=kw.pop('initial_pose',POSE),latency=64,save_frames=False,**kw)[0]


@pytest.mark.parametrize('typ,health,ammo,collected',[(2011,100,50,0),(2012,100,50,0),(2014,101,50,1),(2007,100,60,1),(2048,100,100,1)])
def test_original_item_rules_at_full_health(combat_renderer,monkeypatch,typ,health,ammo,collected):
    fixture_scene(monkeypatch,[(2184,-2392,typ)])
    r=run(combat_renderer,[{}]*4)
    f=r['frames'][-1]
    assert (f['combat']['health'],f['combat']['ammo'])==(health,ammo)
    assert f['pickups']['stats']['collected']==collected
    assert f['pickups']['items'][0]['active']==(not collected)
    assert r['stack_wraps']==r['ddr']['invalid']==r['ddr']['hazards']==0


@pytest.mark.parametrize('typ,health,added',[(2011,100,10),(2012,100,10),(2014,91,1)])
def test_health_is_restored_after_native_damage_with_effective_caps(combat_renderer,monkeypatch,typ,health,added):
    fixture_scene(monkeypatch,[(2184,-2392,typ)],[(2216,-2392,20)],frame=4,tics=7,awake=1)
    r=run(combat_renderer,[{}]*3);f=r['frames']
    if typ!=2014:
        assert f[0]['combat']['health']==90 and f[0]['pickups']['items'][0]['active']
    # A bonus is consumed before the attack; the effective final total is 91.
    assert f[-1]['combat']['health']==health
    assert f[-1]['combat']['damage']==10
    assert f[-1]['pickups']['stats']['health_added']==added
    assert f[-1]['pickups']['stats']['collected']==1


def test_full_ammo_leaves_item_until_space_is_available(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2184,-2392,2048)]*4)
    r=run(combat_renderer,[{},{}]+[dict(buttons=2)]*3);f=r['frames']
    assert f[1]['combat']['ammo']==200 and f[1]['pickups']['stats']['collected']==3
    assert sum(p['active'] for p in f[1]['pickups']['items'])==1
    assert f[-1]['combat']['ammo']==200 and f[-1]['combat']['shots']==1
    assert f[-1]['pickups']['stats']['collected']==4 and f[-1]['pickups']['stats']['ammo_added']==151


def test_bonus_health_caps_at_200_and_does_not_consume_excess(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2184,-2392,2014)]*101)
    r=run(combat_renderer,[{}]*2);f=r['frames'][-1]
    assert f['combat']['health']==200
    assert f['pickups']['stats']['health_added']==f['pickups']['stats']['collected']==100
    assert sum(p['active'] for p in f['pickups']['items'])==1
    assert r['stack_wraps']==0


def test_contact_collects_once_and_full_health_items_do_not_block(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2224,-2392,2007),(2224,-2392,2012)])
    commands=[dict(forward=4)]*16+[dict(forward=-4)]*16
    r=run(combat_renderer,commands);f=r['frames']
    assert any(s['motion']['x']>2244*65536 for s in f)
    assert f[-1]['combat']['ammo']==60
    assert f[-1]['pickups']['stats']['collected']==1
    assert [p['active'] for p in f[-1]['pickups']['items']]==[False,True]
    assert any(s['pickups']['stats']['flash'] for s in f)
    assert f[-1]['pickups']['stats']['flash']==0


def test_nearby_wall_blocks_collection(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2202,-2392,2007)])
    original=A.pack
    def wall(*args,**kw):
        boot,assets=original(*args,**kw)
        # Initial synthetic collision world: player is 17 units from the wall,
        # item is one unit beyond it and still within the 20-unit touch box.
        for i in range(assets['lines']):struct.pack_into('<6h4B',args[2],0x80010+i*16,2201,-2500,2201,-2300,0,0,1,0,255,0)
        return boot,assets
    monkeypatch.setattr(A,'pack',wall)
    r=run(combat_renderer,[{}]*2);f=r['frames'][-1]
    assert f['combat']['ammo']==50 and f['pickups']['stats']['collected']==0
    assert f['pickups']['items'][0]['active']


def test_health_item_cannot_revive_a_dead_player(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2184,-2392,2012)],[(2216,-2392,20)]*10,frame=4,tics=7,awake=1)
    r=run(combat_renderer,[{}]*4)
    assert all(f['combat']['dead'] and f['combat']['health']==0 for f in r['frames'])
    assert all(f['pickups']['stats']['collected']==0 and f['pickups']['items'][0]['active'] for f in r['frames'])


def test_loader_filters_skill_multiplayer_and_old_format(combat_renderer):
    import doom_sim as S
    wad,out=combat_renderer;image=bytearray(S.load_ihx(out/'doom_renderer.ihx'))
    rows=[(2011,2),(2012,1),(2014,18),(2007,2),(2048,2)]
    raw=b''.join(struct.pack('<hhHHH',2272,-2392,0,t,flags) for t,flags in rows)
    for version,wanted in ((6,3),(5,0)):
        image[0xFFF4]=version;loads={}
        def load(address,data,label):loads[address]=bytes(data);return address
        assets=A.pack_monsters(A.Wad(wad),raw,image,load)
        assert assets['pickups']['count']==wanted
        if wanted:assert [t['type'] for t in assets['pickups']['things']]==[2011,2007,2048]


def test_original_map_pickups_and_limit_are_explicit(combat_renderer):
    import doom_sim as S
    wad,out=combat_renderer;image=S.load_ihx(out/'doom_renderer.ihx');w=A.Wad(wad)
    i=next(i for i,(n,_) in enumerate(w.lumps) if n=='E1M1')
    rows=A.fields(w.lumps[i+1][1],'<hhHHH');expected=[r for r in rows if r[3] in A.PICKUPS and r[4]&2 and not r[4]&16]
    loaded={}
    def load(address,data,label):loaded[address]=bytes(data);return address
    assets=A.pack_monsters(w,w.lumps[i+1][1],image,load)
    assert assets['pickups']['count']==len(expected)==19
    assert struct.unpack_from('<H',loaded[0xD8010])[0]==19
    assert {r['type'] for r in assets['pickups']['things']}=={t for t,(_,rule) in A.PICKUPS.items() if rule<5}
    raw=struct.pack('<hhHHH',2184,-2392,0,2007,2)*129
    with pytest.raises(ValueError,match='pickup limit'):A.pack_monsters(w,raw,image,load)


def test_pickup_above_player_body_is_not_collected(combat_renderer,monkeypatch):
    fixture_scene(monkeypatch,[(2172,-2392,2007)])
    original=A.pack
    def high_platform(*args,**kw):
        boot,assets=original(*args,**kw);memory=args[2]
        size,fo,co=assets['schema'][:3]
        # Raise the adjacent 8-unit stair sector above the player's body.
        # The player touches its boundary without penetrating it. The item's
        # sight ray is above the portal floor, so height is the rejecting rule.
        for i in range(assets['sectors']):
            p=0x20010+i*size+fo
            if struct.unpack_from('<i',memory,p)[0]==8*65536:struct.pack_into('<i',memory,p,80*65536)
        for i in range(assets['lines']):
            p=0x80010+i*16;front,back=memory[p+13],memory[p+14]
            if back==255 or memory[p+12]&1:continue
            floors=[struct.unpack_from('<i',memory,0x20010+s*size+fo)[0]>>16 for s in (front,back)]
            struct.pack_into('<h',memory,p+8,max(floors))
        return boot,assets
    monkeypatch.setattr(A,'pack',high_platform)
    pose=dict(POSE,x=2192*65536)
    r=run(combat_renderer,[{}],initial_pose=pose);f=r['frames'][0]
    assert f['pickups']['items'][0]['floor']==80 and f['motion']['floor']==16
    assert f['combat']['ammo']==50 and f['pickups']['items'][0]['active']


def test_original_ammo_clip_pixels_are_drawn_by_cpu(combat_renderer,monkeypatch):
    from PIL import Image
    wad,out=combat_renderer
    with monkeypatch.context() as m:
        fixture_scene(m,[]);run(combat_renderer,[{}],hud=False)
        expected=Image.open(out/'e1m1-native.png').copy()
    with monkeypatch.context() as m:
        fixture_scene(m,[(2272,-2392,2007)])
        r=run(combat_renderer,[{}],hud=False)
        actual=Image.open(out/'e1m1-native.png').copy()
    w=A.Wad(wad);raw=w['CLIPA0'];width,height,left,top=struct.unpack_from('<4h',raw);pixels={}
    for x in range(width):
        offset=struct.unpack_from('<I',raw,8+x*4)[0]
        while raw[offset]!=255:
            y0,count=raw[offset:offset+2]
            for y,c in enumerate(raw[offset+3:offset+3+count],y0):pixels[x,y]=c
            offset+=count+4
    # Independent fixed-point projection and raw WAD post decoder. The host
    # checks the capture; it never feeds these projected pixels to the CPU.
    xs=15*65536//87;ys=64*65536//87
    screen_left=15*65536+(((88*25-left*65536)*xs)>>16)
    screen_top=32*65536-(24+top-57)*ys
    xstep=(1<<32)//xs;ystep=(1<<32)//ys;count=0;palette=w['PLAYPAL']
    for x in range(30):
        for y in range(64):
            if x<screen_left//65536 or y<screen_top//65536:continue
            sx=(((x*65536-screen_left)*xstep)>>16)>>16
            sy=(((y*65536-screen_top)*ystep)>>16)>>16
            c=pixels.get((sx,sy))
            if c is not None:expected.putpixel((x,y),tuple(palette[c*3:c*3+3]));count+=1
    assert count==r['frames'][0]['sprites']['pixels']>0
    assert actual.tobytes()==expected.tobytes()
