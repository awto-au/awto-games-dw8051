"""Original normal/secret exit use, native completion and frozen gameplay."""
import json,struct
import pytest
from PIL import Image
from test_doom_motion import motion_image,Player
from test_doom_doors import door_player,door
from test_doom_combat import combat_renderer,POSE
from test_doom_pickups import fixture_scene
import doom_assets as A,doom_renderer as R,doom_sim as S


def exit_state(p):return dict(zip(('kind','line','activations','reserved'),struct.unpack('<4H',p.c.xram[0xF770:0xF778])))


@pytest.mark.parametrize('kind',[1,2])
@pytest.mark.parametrize('door_count',[0,1])
def test_exit_is_one_shot_and_freezes_native_controller(motion_image,kind,door_count):
    p=door_player(motion_image,switch=True,targets=0,exit_kind=kind,door_count=door_count)
    try:
        first=p.frame(buttons=1)
        assert exit_state(p)==dict(kind=kind,line=0,activations=1,reserved=0)
        assert struct.unpack_from('<h',p.c.ddr_mem(),0xB0010)[0]==8
        before=bytes(p.c.xram[0xF748:0xF778])
        for enabled in (1,0,1):
            after=p.frame(forward=8,strafe=8,turn=4096,buttons=3,enabled=enabled)
            assert all(after[k]==first[k] for k in ('x','y','angle','floor','ceiling','ticks'))
            assert after['frame_ticks']==0
            assert bytes(p.c.xram[0xF748:0xF778])==before
    finally:p.free()


@pytest.mark.parametrize('x,angle',[(-8,0),(128,1<<31)])
def test_exit_use_respects_range_and_front_side(motion_image,x,angle):
    p=door_player(motion_image,switch=True,targets=0,exit_kind=1,x=x,angle=angle)
    try:
        p.frame(buttons=1)
        assert exit_state(p)['kind']==0 and exit_state(p)['line']==65535
    finally:p.free()


def test_a_nearer_wall_blocks_exit_use(motion_image):
    p=Player(motion_image,[(64,128,64,-128,0,0,2),(32,128,32,-128,0,0,1)],ceiling_b=0,door=True,switch=True,targets=0,exit_kind=1)
    try:
        p.frame(buttons=1)
        assert exit_state(p)['activations']==0
    finally:p.free()


def pose():return json.loads((R.ROOT/'examples/doom-exit-pose.json').read_text())


def test_original_e1m1_exit_completes_and_rejects_later_input(combat_renderer):
    wad,out=combat_renderer;commands=json.loads((R.ROOT/'examples/doom-exit-demo.json').read_text())
    r,_=R.simulate(wad,out,initial_pose=pose(),commands=commands,frames=len(commands),latency=64)
    f=r['frames'];done=next(i for i,s in enumerate(f) if s['exit']['kind'])
    assert done==20 and f[done]['exit']['line']==330
    assert f[-1]['exit']['kind']==f[-1]['exit']['activations']==1
    assert f[-1]['combat']['shots']==0
    assert all(s['motion']['frame_ticks']==0 for s in f[done+1:])
    assert Image.open(out/f'frame-{done:03d}.png').tobytes()==Image.open(out/f'frame-{len(f)-1:03d}.png').tobytes()
    assert r['stack_wraps']==r['ddr']['invalid']==r['ddr']['hazards']==0


def test_secret_exit_state_and_native_banner_pixels(combat_renderer):
    wad,out=combat_renderer;p=dict(pose(),x=2960*65536)
    r,_=R.simulate(wad,out,initial_pose=p,scene=dict(line_specials={'330':51}),commands=[dict(buttons=1)],frames=1,latency=64)
    f=r['frames'][0];assert f['exit']['kind']==2 and f['exit']['line']==330
    assert f['doors']['activations']==0
    assert f['switches']['stats']['consumed']!=0
    image=Image.open(out/'e1m1-native.png');palette=A.Wad(wad)['PLAYPAL']
    glyphs=['111100110100111','101101010101101','111010010010111','111010010010010']
    for k,glyph in enumerate(glyphs):
        for y in range(5):
            for x in range(3):
                c=4 if glyph[y*3+x]=='1' else 0
                assert image.getpixel((15-7+k*4+x,8+y))==tuple(palette[c*3:c*3+3])


def test_loader_original_exit_and_older_format(combat_renderer):
    wad,out=combat_renderer;image=bytearray(S.load_ihx(out/'doom_renderer.ihx'));memory=bytearray(32*1024*1024)
    _,assets=A.pack(wad,image,memory,out)
    exits=[s for s in assets['switches'] if s['kind']]
    assert len(exits)==1 and exits[0]['line']==330 and exits[0]['kind']==1 and exits[0]['mask']==0
    image[0xFFF4]=8
    _,old=A.pack(wad,image,memory,out)
    assert not any(s['kind'] for s in old['switches'])
    assert memory[0x80010+330*16+15]==0


def test_a_dead_player_cannot_finish_the_level(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_scene(monkeypatch,[],[(1504,-2480,20)]*10,frame=4,tics=7,awake=1)
    p=dict(x=1504*65536,y=-2512*65536,angle=3<<30,viewz=41*65536)
    r,_=R.simulate(wad,out,initial_pose=p,scene=dict(line_specials={'153':11}),commands=[{}]+[dict(buttons=1)]*3,frames=4,latency=64,save_frames=False)
    assert all(f['combat']['dead'] and f['exit']['kind']==0 for f in r['frames'])


def test_exit_freezes_a_fireball_already_in_flight(combat_renderer,monkeypatch):
    wad,out=combat_renderer
    fixture_scene(monkeypatch,[],[(2272,-2392,20)])
    original=A.pack
    def transparent_use_plane(*args,**kw):
        boot,assets=original(*args,**kw)
        # Initial collision fixture. Every indexed profile is a transparent
        # use plane, so the existing BLOCKMAP cannot hide the test exit ray.
        for i in range(assets['lines']):struct.pack_into('<6h4B',args[2],0x80010+i*16,2232,-2320,2232,-2460,0,128,0,0,255,17)
        return boot,assets
    monkeypatch.setattr(A,'pack',transparent_use_plane)
    commands=[{}]*29+[dict(buttons=1)]+[dict(forward=8,buttons=3)]*10
    r,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),latency=64,save_frames=False)
    f=r['frames'];assert any(s['active'] and s['phase']==1 for s in f[28]['projectiles']['slots'])
    assert f[29]['exit']['kind']==1
    assert f[29]['projectiles']==f[-1]['projectiles']
    assert f[29]['actors']==f[-1]['actors'] and f[-1]['combat']['shots']==0


def test_render_only_yaw_cannot_rotate_a_completed_level(combat_renderer):
    wad,out=combat_renderer;p=dict(pose(),x=2960*65536)
    commands=[dict(buttons=1)]+[dict(enabled=0)]*3
    r,_=R.simulate(wad,out,initial_pose=p,commands=commands,frames=4,yaw_step=45,latency=64)
    assert r['frames'][-1]['motion']['angle']==r['frames'][0]['motion']['angle']
    assert Image.open(out/'frame-000.png').tobytes()==Image.open(out/'frame-003.png').tobytes()


def test_highest_exit_slot_does_not_alias_a_manual_lock(motion_image):
    p=door_player(motion_image,switch=True,targets=0,exit_kind=2,door_count=0,switch_index=14)
    try:
        p.frame(buttons=1)
        assert exit_state(p)['kind']==2 and exit_state(p)['activations']==1
        assert struct.unpack_from('<H',p.c.xram,0xF754)[0]==1<<14
        assert struct.unpack_from('<H',p.c.xram,0xF756)[0]==15
    finally:p.free()


def test_combined_switch_exit_capacity_and_real_last_slot(combat_renderer):
    wad,out=combat_renderer
    s=dict(line_specials={str(i):63 for i in range(14)},line_tags={str(i):123 for i in range(14)},sector_tags={'4':123})
    p=dict(pose(),x=2960*65536)
    r,_=R.simulate(wad,out,initial_pose=p,scene=s,commands=[dict(buttons=1)],frames=1,latency=64)
    assert len(r['assets']['switches'])==15
    assert r['assets']['switches'][-1]['line']==330 and r['assets']['switches'][-1]['kind']==1
    assert r['frames'][0]['exit']['kind']==1 and r['frames'][0]['switches']['stats']['last']==15
