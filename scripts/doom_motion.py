"""Input serialization and independent collision checks, never player physics.

Commands go into the native mailbox. The geometric oracle only checks the
completed native pose, using all static map lines rather than its BLOCKMAP.
"""
import struct
from fractions import Fraction
INPUT_BASE=0xF610
STATE_BASE=0xF6A0
INPUT=struct.Struct('<bbhBB')
STATE=struct.Struct('<iiIhhIBBBB')
STATE_KEYS=('x','y','angle','floor','ceiling','ticks','blocked','frame_ticks','fault','enabled')
LINES_BASE=0x80010


def pack_command(command):
    return INPUT.pack(command.get('forward',0),command.get('strafe',0),command.get('turn',0),command.get('enabled',1),command.get('buttons',0))


def unpack_state(raw):return dict(zip(STATE_KEYS,STATE.unpack(raw)))


def crosses_open_box(x1,y1,x2,y2,left,right,bottom,top):
    """Exact rational segment/box clipping, independent of native corner signs."""
    lo,hi=Fraction(0),Fraction(1)
    for start,delta,a,b in ((x1,x2-x1,left,right),(y1,y2-y1,bottom,top)):
        if not delta:
            if not a<start<b:return False
            continue
        t1,t2=Fraction(a-start,delta),Fraction(b-start,delta)
        if t1>t2:t1,t2=t2,t1
        lo,hi=max(lo,t1),min(hi,t2)
        if lo>=hi:return False
    return True


def validate_pose(state,profiles,previous=None):
    assert state['fault']==0
    assert state['ceiling']-state['floor']>=56,('headroom',state)
    x,y=state['x'],state['y'];radius=16*65536
    for i,(x1,y1,x2,y2,bottom,top,solid) in enumerate(profiles):
        if not (solid&1) and bottom<=state['floor'] and top>=state['floor']+56:continue
        assert not crosses_open_box(x1*65536,y1*65536,x2*65536,y2*65536,x-radius,x+radius,y-radius,y+radius),('penetration',i,state)
    if previous is not None:
        limit=state['frame_ticks']*16*65536
        assert abs(x-previous['x'])<=limit and abs(y-previous['y'])<=limit,('movement bound',previous,state)
    return True


def read_profiles(memory,count):
    return [row[:7] for row in struct.iter_unpack('<6h4B',memory[LINES_BASE:LINES_BASE+count*16])]


def verify_profiles(memory,assets):
    schema=assets['schema'];size,fo,co=schema[0],schema[1],schema[2]
    for row in struct.iter_unpack('<6h4B',memory[LINES_BASE:LINES_BASE+assets['lines']*16]):
        x1,y1,x2,y2,bottom,top,flags,front,back,token=row
        if flags&1 or back==255 or (x1,y1)==(x2,y2):continue
        heights=[]
        for sector in (front,back):
            addr=0x20010+sector*size
            heights.append((struct.unpack_from('<i',memory,addr+fo)[0]>>16,struct.unpack_from('<i',memory,addr+co)[0]>>16))
        assert bottom==max(h[0] for h in heights) and top==min(h[1] for h in heights),('stale collision profile',row,heights)
    return True


def read_doors(xram):
    count,last,reopens,fault,activations,updates=struct.unpack('<4B2H',xram[0xF6C0:0xF6C8])
    assert fault==0,('door fault',fault)
    states=[dict(zip(('height','wait','phase','stay','reserved'),struct.unpack_from('<hHBBH',xram,0xF200+i*8))) for i in range(count)]
    return dict(count=count,fault=fault,last_used=last,reopens=reopens,activations=activations,updates=updates,states=states)
