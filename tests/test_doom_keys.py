"""Native key inventory, coloured manual locks and initial-scene loading."""
import json,struct
from pathlib import Path
import pytest
from test_doom_motion import motion_image,Player
from test_doom_doors import door_player,door
from test_doom_combat import combat_renderer,POSE
from test_doom_pickups import fixture_scene,run
import doom_assets as A,doom_renderer as R


def keys(p):return dict(zip(('owned','needed','denied','notice'),struct.unpack('<4H',p.c.xram[0xF748:0xF750])))


@pytest.mark.parametrize('colour',[1,2,3])
@pytest.mark.parametrize('owned',[0,1,2,4,8,16,32])
def test_matching_card_or_skull_opens_only_its_colour(motion_image,colour,owned):
    p=door_player(motion_image,keys=owned,lock=colour)
    try:
        p.frame(buttons=1);opened=bool(owned&((1<<(colour-1))|(8<<(colour-1))))
        assert (door(p)['activations']==1)==opened
        assert door(p)['states'][0]['height']==(2 if opened else 0)
        k=keys(p);assert k['owned']==owned  # opening never consumes the key
        assert k['denied']==(not opened)
        assert k['needed']==(0 if opened else 1<<(colour-1))
    finally:p.free()


@pytest.mark.parametrize('stay',[False,True])
def test_keyed_door_retains_wait_close_or_stay_behaviour(motion_image,stay):
    p=door_player(motion_image,keys=8,lock=1,stay=stay)
    try:
        for _ in range(210):p.frame(buttons=1)
        d=door(p)
        assert d['activations']==1
        assert d['states'][0]['height']==(124 if stay else 0)
        assert d['states'][0]['phase']==(4 if stay else 0)
        assert keys(p)['owned']==8
    finally:p.free()


def test_rejected_use_is_edge_triggered_and_notice_expires(motion_image):
    p=door_player(motion_image,lock=2)
    try:
        for _ in range(10):p.frame(buttons=1)
        assert keys(p)['denied']==1 and keys(p)['needed']==2
        p.frame();p.frame(buttons=1)
        assert keys(p)['denied']==2
        for _ in range(30):p.frame()
        assert keys(p)['notice']==keys(p)['needed']==0
        assert door(p)['activations']==0
    finally:p.free()


def test_wall_in_front_of_lock_does_not_emit_a_key_request(motion_image):
    p=Player(motion_image,[(64,128,64,-128,0,0,2),(32,128,32,-128,0,0,1)],ceiling_b=0,door=True,lock=3)
    try:
        p.frame(buttons=1)
        assert keys(p)['denied']==keys(p)['needed']==0
        assert door(p)['activations']==0
    finally:p.free()


def fixture_keys(monkeypatch,items,overrides=()):
    original=A.pack_monsters
    def with_cards(wad,things,image,load):
        # Only initial assets: ensure the shareware card patches are available.
        extra=b''.join(struct.pack('<hhHHH',1456,-2496,0,t,2) for t in (5,6,13))
        return original(wad,things+extra,image,load)
    monkeypatch.setattr(A,'pack_monsters',with_cards)
    fixture_scene(monkeypatch,items)
    if overrides:
        original_pack=A.pack
        def rules(*args,**kw):
            boot,assets=original_pack(*args,**kw)
            for i,rule in enumerate(overrides):
                struct.pack_into('<H',args[2],0xD0020+(8+i)*20+12,rule)
                assets['monsters']['pickups']['things'][i]['rule']=rule
            return boot,assets
        monkeypatch.setattr(A,'pack',rules)


@pytest.mark.parametrize('rule',list(range(5,11)))
def test_native_collection_and_hud_keep_six_distinct_key_bits(combat_renderer,monkeypatch,rule):
    from PIL import Image
    colour=(rule-5)%3;typ=(5,6,13)[colour]
    # Skull inventory uses a card picture in this logic fixture: the shareware
    # IWAD does not contain skull-key artwork. No replacement is shipped.
    fixture_keys(monkeypatch,[(2184,-2392,typ)],overrides=[rule])
    r=run(combat_renderer,[{}]*4);f=r['frames'][-1]
    assert f['inventory']['keys']==1<<(rule-5)
    assert f['pickups']['stats']['collected']==1 and not f['pickups']['items'][0]['active']
    assert f['combat']['health']==100 and f['combat']['ammo']==50
    assert f['pickups']['stats']['health_added']==f['pickups']['stats']['ammo_added']==0
    palette=A.Wad(combat_renderer[0])['PLAYPAL'];c=(200,160,176)[colour]
    image=Image.open(combat_renderer[1]/'e1m1-native.png')
    for x in range(3):
        for y in range(3):assert image.getpixel((2+colour*5+x,2+y))==tuple(palette[c*3:c*3+3])
    assert r['stack_wraps']==r['ddr']['invalid']==r['ddr']['hazards']==0


@pytest.mark.parametrize('rules,owned,collected',[([5,5],1,1),([5,8],9,2)])
def test_duplicate_keys_remain_but_card_and_skull_are_distinct(combat_renderer,monkeypatch,rules,owned,collected):
    fixture_keys(monkeypatch,[(2184,-2392,5)]*2,overrides=rules)
    r=run(combat_renderer,[{}]*3);f=r['frames'][-1]
    assert f['inventory']['keys']==owned and f['pickups']['stats']['collected']==collected
    assert sum(p['active'] for p in f['pickups']['items'])==2-collected


def test_use_rejects_then_collected_key_opens_real_door_geometry(combat_renderer):
    wad,out=combat_renderer
    scene=json.loads((R.ROOT/'examples/doom-keys-scene.json').read_text())
    pose=json.loads((R.ROOT/'examples/doom-keys-pose.json').read_text())
    commands=json.loads((R.ROOT/'examples/doom-keys-demo.json').read_text())
    r,_=R.simulate(wad,out,initial_pose=pose,scene=scene,commands=commands,frames=len(commands),latency=64,save_frames=False)
    f=r['frames']
    assert f[0]['inventory']['denied']==1 and f[0]['inventory']['needed']==1
    assert f[0]['doors']['activations']==0
    assert any(s['inventory']['keys']==1 and s['doors']['activations']==0 for s in f)
    assert f[-1]['inventory']['keys']==1 and f[-1]['inventory']['denied']==1
    assert f[-1]['doors']['activations']==1 and f[-1]['motion']['x']>1552*65536
    assert all(s['inventory']['verified'] and s['world_verified'] for s in f)
    assert r['stack_wraps']==0


@pytest.mark.parametrize('special,colour,stay',[(26,1,False),(27,2,False),(28,3,False),(32,1,True),(33,3,True),(34,2,True)])
def test_original_special_numbers_pack_per_line_lock_tokens(combat_renderer,special,colour,stay):
    import doom_sim as S
    wad,out=combat_renderer;mem=bytearray(32*1024*1024)
    scene=dict(line_specials={'151':special})
    _,assets=A.pack(wad,S.load_ihx(out/'doom_renderer.ihx'),mem,out,scene=scene)
    token=mem[0x80010+151*16+15]
    assert token&31 and (token>>5)&3==colour and bool(token&128)==stay
    # Another use edge targeting that same sector stays independently unlocked.
    assert (mem[0x80010+152*16+15]>>5)&3==0


def test_old_format_does_not_load_keys_or_unlock_locked_specials(combat_renderer):
    import doom_sim as S
    wad,out=combat_renderer;image=bytearray(S.load_ihx(out/'doom_renderer.ihx'));image[0xFFF4]=6
    loads={}
    def load(a,data,label):loads[a]=bytes(data);return a
    raw=struct.pack('<hhHHH',1456,-2496,0,5,2)
    packed=A.pack_monsters(A.Wad(wad),raw,image,load)
    assert packed['pickups']['count']==0
    with pytest.raises(ValueError,match='format 7'):A.pack(wad,image,bytearray(32*1024*1024),out,scene=dict(line_specials={'151':26}))


def test_holding_denied_use_does_not_auto_unlock_on_key_collection(combat_renderer):
    wad,out=combat_renderer
    scene=json.loads((R.ROOT/'examples/doom-keys-scene.json').read_text())
    pose=json.loads((R.ROOT/'examples/doom-keys-pose.json').read_text())
    commands=[dict(buttons=1)]*2+[dict(buttons=1,forward=-4)]*5+[dict(buttons=1,forward=4)]*5+[dict(buttons=1)]*4+[{},dict(buttons=1)]+[{}]*30
    r,_=R.simulate(wad,out,initial_pose=pose,scene=scene,commands=commands,frames=len(commands),latency=64,save_frames=False)
    f=r['frames']
    assert f[15]['inventory']['keys']==1 and f[15]['doors']['activations']==0
    assert f[15]['inventory']['denied']==1
    assert f[-1]['doors']['activations']==1 and f[-1]['inventory']['keys']==1
