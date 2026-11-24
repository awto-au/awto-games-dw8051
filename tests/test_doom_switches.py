"""Native tagged door targets, switch textures and button rearming."""
import json,struct
import pytest
from PIL import Image
from test_doom_motion import motion_image,Player
from test_doom_doors import door_player,door
from test_doom_combat import combat_renderer
import doom_assets as A,doom_renderer as R,doom_sim as S


def switch(p):return dict(zip(('activations','resets','consumed','last'),struct.unpack('<4H',p.c.xram[0xF750:0xF758])))
def texture(p):return struct.unpack_from('<h',p.c.ddr_mem(),0xB0010)[0]


@pytest.mark.parametrize('repeat',[False,True])
@pytest.mark.parametrize('stay',[False,True])
def test_native_one_shot_repeat_reset_and_door_action(motion_image,repeat,stay):
    p=door_player(motion_image,switch=True,repeat=repeat,stay=stay)
    try:
        p.frame(buttons=1)
        assert switch(p)['activations']==1 and texture(p)==8
        for _ in range(39):p.frame(buttons=1)
        assert switch(p)['activations']==1  # held use cannot rearm itself
        assert texture(p)==(7 if repeat else 8)
        p.frame();p.frame(buttons=1)
        assert switch(p)['activations']==(2 if repeat else 1)
        for _ in range(210):p.frame()
        assert door(p)['states'][0]['height']==(124 if stay else 0)
        assert switch(p)['resets']==(2 if repeat else 0)
        assert switch(p)['consumed']==(0 if repeat else 1)
    finally:p.free()


def test_empty_target_mask_does_not_consume_or_change_texture(motion_image):
    p=door_player(motion_image,switch=True,targets=0)
    try:
        p.frame(buttons=1)
        assert switch(p)['activations']==switch(p)['consumed']==0
        assert door(p)['activations']==0 and texture(p)==7
    finally:p.free()


@pytest.mark.parametrize('x,angle',[(-8,0),(128,1<<31)])
def test_switch_range_and_front_side_still_apply(motion_image,x,angle):
    p=door_player(motion_image,switch=True,x=x,angle=angle)
    try:
        p.frame(buttons=1)
        assert switch(p)['activations']==0 and texture(p)==7
    finally:p.free()


def test_nearer_wall_blocks_a_switch(motion_image):
    p=Player(motion_image,[(64,128,64,-128,0,0,2),(32,128,32,-128,0,0,1)],ceiling_b=0,door=True,switch=True)
    try:
        p.frame(buttons=1)
        assert switch(p)['activations']==door(p)['activations']==0
    finally:p.free()


def scene(special=63):
    s=json.loads((R.ROOT/'examples/doom-switch-scene.json').read_text());s['line_specials']['153']=special;return s

def pose():return json.loads((R.ROOT/'examples/doom-switch-pose.json').read_text())


@pytest.mark.parametrize('special,repeat,stay',[(29,False,False),(63,True,False),(103,False,True),(61,True,True)])
def test_original_switch_specials_pack_target_mask_and_style(combat_renderer,special,repeat,stay):
    wad,out=combat_renderer;memory=bytearray(32*1024*1024)
    _,assets=A.pack(wad,S.load_ihx(out/'doom_renderer.ihx'),memory,out,scene=scene(special))
    sw=assets['switches'][0];token=memory[0x80010+153*16+15]
    assert token&31==17 and bool(token&32)==repeat and bool(token&128)==stay
    assert sw['repeat']==repeat and sw['stay']==stay
    assert sw['mask']==1 and sw['targets']==[4] and sw['texture']>0 and sw['off']!=sw['on']


def test_one_tag_activates_multiple_real_sectors(combat_renderer):
    wad,out=combat_renderer;s=scene();s['sector_tags']['20']=123
    r,_=R.simulate(wad,out,scene=s,initial_pose=pose(),commands=[dict(buttons=1)],latency=64)
    sw=r['assets']['switches'][0]
    assert len(sw['targets'])==2 and sw['mask'].bit_count()==2
    assert r['frames'][0]['doors']['activations']==2
    assert r['frames'][0]['switches']['stats']['activations']==1
    assert r['frames'][0]['switches']['verified']


@pytest.mark.parametrize('tag',[0,124])
def test_zero_and_unmatched_tags_cannot_broadcast(combat_renderer,tag):
    wad,out=combat_renderer;s=scene();s['line_tags']['153']=tag
    r,_=R.simulate(wad,out,scene=s,initial_pose=pose(),commands=[dict(buttons=1)],latency=64)
    assert all(s['line']!=153 for s in r['assets']['switches'])
    assert r['frames'][0]['doors']['activations']==0


def test_original_switch_texture_pixels_change_and_reset_natively(combat_renderer):
    wad,out=combat_renderer
    r,_=R.simulate(wad,out,scene=scene(),initial_pose=pose(),commands=[{},dict(buttons=1)]+[{}]*30,frames=32,latency=64)
    off=Image.open(out/'frame-000.png').crop((8,10,22,50)).tobytes()
    on=Image.open(out/'frame-001.png').crop((8,10,22,50)).tobytes()
    assert on!=off
    assert r['frames'][-1]['switches']['stats']['resets']==1
    assert Image.open(out/'frame-031.png').crop((8,10,22,50)).tobytes()==off
    static=scene();static['side_textures']['211']['middle']='SW2STRTN'
    R.simulate(wad,out,scene=static,initial_pose=pose(),commands=[{}],latency=64)
    # Independent boot with the original SW2 texture, not a host pixel overlay.
    assert Image.open(out/'e1m1-native.png').crop((8,10,22,50)).tobytes()==on


def test_switch_walkthrough_opens_a_remote_door_and_passes(combat_renderer):
    wad,out=combat_renderer;commands=json.loads((R.ROOT/'examples/doom-switch-demo.json').read_text())
    r,_=R.simulate(wad,out,scene=scene(),initial_pose=pose(),commands=commands,frames=len(commands),latency=64,save_frames=False)
    f=r['frames']
    assert f[0]['doors']['activations']==0
    assert f[-1]['switches']['stats']['activations']==f[-1]['switches']['stats']['resets']==1
    assert f[-1]['motion']['x']>1552*65536
    assert r['stack_wraps']==0


def test_switch_capacity_and_legacy_scene_guard(combat_renderer):
    wad,out=combat_renderer;image=bytearray(S.load_ihx(out/'doom_renderer.ihx'))
    s=scene();s['line_specials']={str(i):63 for i in range(16)};s['line_tags']={str(i):123 for i in range(16)}
    with pytest.raises(ValueError,match='too many standalone switches'):A.pack(wad,image,bytearray(32*1024*1024),out,scene=s)
    image[0xFFF4]=7
    with pytest.raises(ValueError):A.pack(wad,image,bytearray(32*1024*1024),out,scene=scene())


def test_reusable_button_rejects_a_new_press_until_reset(motion_image):
    p=door_player(motion_image,switch=True,repeat=True)
    try:
        p.frame(buttons=1);p.frame();p.frame(buttons=1)
        assert switch(p)['activations']==1 and texture(p)==8
        for _ in range(30):p.frame()
        assert texture(p)==7
        p.frame(buttons=1)
        assert switch(p)['activations']==2
    finally:p.free()


@pytest.mark.parametrize('repeat',[False,True])
def test_highest_switch_token_and_bit_do_not_alias_a_manual_lock(motion_image,repeat):
    p=door_player(motion_image,switch=True,repeat=repeat,stay=True,switch_index=14)
    try:
        p.frame(buttons=1)
        state=switch(p)
        assert state['activations']==1 and state['last']==15
        assert state['consumed']==(0 if repeat else 1<<14)
        assert door(p)['activations']==1 and door(p)['states'][0]['stay']==1
        assert struct.unpack_from('<h',p.c.ddr_mem(),0xB0010+28)[0]==8
        assert struct.unpack_from('<h',p.c.ddr_mem(),0xB0010)[0]==7
        assert struct.unpack_from('<H',p.c.xram,0xF74C)[0]==0  # no key denial
    finally:p.free()
