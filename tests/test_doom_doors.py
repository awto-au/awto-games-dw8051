"""Door actions run as native 8051 code through the input mailbox."""
import struct
import pytest
from test_doom_motion import motion_image,Player
import doom_motion as M

def door_player(image,**kw):
    # Clockwise segment: its front faces the player at x=0.
    return Player(image,[(64,128,64,-128,0,0,2)],ceiling_b=0,door=True,**kw)

def door(p):
    result=M.read_doors(p.c.xram)
    assert result['fault']==0
    assert struct.unpack_from('<h',p.c.ddr_mem(),0x80010+10)[0]==result['states'][0]['height']
    return result

def test_open_wait_and_close(motion_image):
    p=door_player(motion_image)
    try:
        p.frame(buttons=1)
        assert door(p)['states'][0]['phase']==1
        assert door(p)['states'][0]['height']==2
        for _ in range(30):p.frame()
        r=door(p);assert r['states'][0]['height']==86 and r['states'][0]['phase']==1
        for _ in range(20):p.frame()
        assert door(p)['states'][0]['phase']==2
        for _ in range(170):p.frame()
        r=door(p);assert r['states'][0]['height']==0 and r['states'][0]['phase']==0
        assert r['activations']==1
    finally:p.free()

def test_player_obstruction_reopens_without_crushing(motion_image):
    p=door_player(motion_image)
    try:
        p.frame(buttons=1)
        for _ in range(50):p.frame()
        for _ in range(7):p.frame(forward=8)
        # Stop in the sector box, then wait for the automatic close attempt.
        assert 64*65536<=p.frame()['x']<=96*65536
        for _ in range(160):
            state=p.frame()
            assert state['ceiling']>=state['floor']+56
        assert door(p)['reopens']>=1
    finally:p.free()

def test_raise_stay_and_use_edge(motion_image):
    p=door_player(motion_image,stay=True)
    try:
        for _ in range(200):p.frame(buttons=1)
        r=door(p);assert r['states'][0]['phase']==4 and r['states'][0]['height']==124
        assert r['activations']==1
    finally:p.free()

def test_use_does_not_pass_a_solid_wall(motion_image):
    p=Player(motion_image,[(64,128,64,-128,0,0,2),(32,128,32,-128,0,0,1)],ceiling_b=0,door=True)
    try:
        p.frame(buttons=1)
        assert door(p)['activations']==0 and door(p)['states'][0]['height']==0
    finally:p.free()

def test_doorway_remains_blocked_until_tall_enough(motion_image):
    p=door_player(motion_image)
    try:
        for _ in range(6):p.frame(forward=8)
        assert p.frame()['x']==48*65536
        p.frame(buttons=1,forward=8)
        for _ in range(12):assert p.frame(forward=8)['x']==48*65536
        for _ in range(20):state=p.frame(forward=4)
        assert state['x']>64*65536
    finally:p.free()

@pytest.mark.parametrize('x,angle',[(-8,0),(128,1<<31)])
def test_use_range_and_front_side(motion_image,x,angle):
    p=door_player(motion_image,x=x,angle=angle)
    try:
        p.frame(buttons=1)
        assert door(p)['activations']==0
    finally:p.free()


def test_use_reverses_a_closing_door(motion_image):
    p=door_player(motion_image)
    try:
        p.frame(buttons=1)
        for _ in range(155):p.frame()
        assert door(p)['states'][0]['phase']==3
        before=door(p)['states'][0]['height']
        p.frame(buttons=1)
        assert door(p)['states'][0]['phase']==1
        assert door(p)['states'][0]['height']>before
    finally:p.free()
