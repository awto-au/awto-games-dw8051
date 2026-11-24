"""Pack original Doom WAD data for SDCC structs. No scene rendering here.

This is offline asset conversion, similar in purpose to Doom8088's jWadUtil.
The WAD is supplied by the user and never included in the source distribution.
"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path


class Wad:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        ident, count, directory = struct.unpack_from("<4sII", self.raw)
        if ident not in (b"IWAD", b"PWAD") or directory + count * 16 > len(self.raw):
            raise ValueError("invalid WAD header/directory")
        self.lumps = []
        for i in range(count):
            off, size, name = struct.unpack_from("<II8s", self.raw, directory + i * 16)
            if off + size > len(self.raw): raise ValueError("WAD lump outside file")
            self.lumps.append((name.rstrip(b"\0").decode("ascii").upper(), self.raw[off:off+size]))
        self.lookup = dict(self.lumps)

    def __getitem__(self, name): return self.lookup[name]


def fields(raw, fmt): return list(struct.iter_unpack(fmt, raw))
def name(raw): return raw.rstrip(b"\0").decode("ascii").upper()

def schema_addresses(image):
    return (0xFF00,0xFF80) if image[0xFFF0:0xFFF4]==b"D805" else (0xF000,0xF080)

MONSTERS = {3004:"POSS",9:"SPOS",3001:"TROO",3002:"SARG",3005:"HEAD",
            3006:"SKUL",3003:"BOSS",16:"CYBR",7:"SPID",58:"SARG"}
# Original thing type -> patch prefix, native rule index.
PICKUPS = {2011:("STIM",0),2012:("MEDI",1),2014:("BON1",2),
           2007:("CLIP",3),2048:("AMMO",4),5:("BKEY",5),6:("YKEY",6),
           13:("RKEY",7),40:("BSKU",8),39:("YSKU",9),38:("RSKU",10)}
# Colour encoding: 0 unlocked, 1 blue, 2 yellow, 3 red. Per linedef.
MANUAL_DOORS={1:(0,False),31:(0,True),26:(1,False),27:(2,False),28:(3,False),
              32:(1,True),34:(2,True),33:(3,True)}
TAGGED_SWITCHES={29:(False,False),63:(False,True),103:(True,False),61:(True,True)}
EXIT_SWITCHES={11:1,51:2}

def pack_monsters(wad, raw_things, image, load):
    """Convert original map things and transparent patches, never visibility."""
    layout=struct.unpack_from("<2H",image,schema_addresses(image)[1])
    combat=image[0xFFF0:0xFFF4]==b"D805"
    if layout not in ((12,16),(20,16)):
        raise ValueError("unexpected native sprite layout")
    projectiles=combat and image[0xFFF4]>=5
    pickup_enabled=combat and image[0xFFF4]>=6
    key_enabled=combat and image[0xFFF4]>=7
    selected=[t for t in fields(raw_things,"<hhHHH") if t[3] in MONSTERS and t[4]&2 and not t[4]&16]
    if len(selected)>128: raise ValueError("static sprite limit is 128 map things")
    types=sorted({t[3] for t in selected})
    kinds={t:i for i,t in enumerate(types)}
    animated=layout[0]==20
    pickup_rows=[t for t in fields(raw_things,"<hhHHH") if t[3] in PICKUPS and (key_enabled or PICKUPS[t[3]][1]<5) and t[4]&2 and not t[4]&16] if pickup_enabled else []
    if len(pickup_rows)>128:raise ValueError("pickup limit is 128 map things")
    pickup_types=sorted({t[3] for t in pickup_rows})
    pickup_kinds={t:len(types)+int(projectiles)+i for i,t in enumerate(pickup_types)}
    pickup_records=b''.join(struct.pack('<hhHHiHBBhH',x,y,0,pickup_kinds[t],0,PICKUPS[t][1],0,0,0,1) for x,y,angle,t,flags in pickup_rows)
    records=b"".join(struct.pack("<hhHHi",x,y,(angle*65536//360)&65535,kinds[t],0)+
                     ((bytes(6)+struct.pack("<H",{3001:60,3002:150,58:150,3003:1000}.get(t,20))) if combat else bytes(8))
                     if animated else struct.pack("<hhHHi",x,y,(angle*65536//360)&65535,kinds[t],0)
                     for x,y,angle,t,_ in selected)
    ranged_kinds=sum(1<<kinds[t] for t in types if t in (3004,9)) if combat and image[0xFFF4]>=4 else 0
    header=struct.pack("<3H10x",len(selected),len(selected)+(8 if projectiles else 0)+len(pickup_rows),len(types)) if projectiles else struct.pack("<HH12x",len(selected),ranged_kinds)
    load(0xD0010,header+records+(bytes(160) if projectiles else b"")+pickup_records,"monster things")
    if pickup_enabled:load(0xD8010,struct.pack('<H14x',len(pickup_rows)),"pickup header")
    if projectiles:
        load(0xD3010,b''.join(struct.pack('<H',2 if t in (3002,58) else int(t in (3001,3003))) for t in types),"monster attack kinds")
        load(0xD6010,bytes(128),"projectile states")
    metadata=bytearray();cursor=0x400010;cached={};patch_records=[]
    for typ in types+([0] if projectiles else [])+pickup_types:
        prefix=PICKUPS[typ][0] if typ in PICKUPS else (MONSTERS[typ] if typ else "BAL1")
        frame_set=("ABCDEFHIJKLM" if typ==3001 else "ABCDEFGHIJKL") if combat else ("ABCD" if animated else "A")
        if not typ:frame_set="ABCDEEEEEEEE"
        if typ in PICKUPS:frame_set="A"*12
        if combat and typ in (3002,58):frame_set="ABCDEGHIKLMN"
        if combat and typ==3003:frame_set="ABCDEGHIKMNO"
        if combat and typ and typ not in (3001,3004,9,3002,58,3003) and typ not in PICKUPS:raise ValueError("monster has no native state mapping")
        for frame in frame_set:
            rotations={}
            for n,raw in wad.lumps:
                if not n.startswith(prefix) or len(n) not in (6,8):continue
                for off in (4,6):
                    if len(n)<=off:continue
                    letter,rot=n[off:off+2]
                    if letter!=frame:continue
                    for r in (range(1,9) if rot=="0" else [int(rot)]):
                        rotations[r]=(n,raw,off==6)
            for rot in range(1,9):
                if rot not in rotations:
                    raise ValueError(f"missing {prefix} {frame} rotation {rot}")
                n,raw,flip=rotations[rot]
                width,height,left,top=struct.unpack_from("<4h",raw)
                if not 0<width<=256 or not 0<height<=128:raise ValueError(f"unsupported sprite size {n}")
                if n not in cached:
                    canvas=bytearray(width*256)
                    for x in range(width):
                        off=struct.unpack_from("<I",raw,8+x*4)[0];previous=-1
                        while raw[off]!=255:
                            y0,length=raw[off],raw[off+1]
                            if y0<=previous:y0+=previous
                            previous=y0
                            for y,c in enumerate(raw[off+3:off+3+length],y0):
                                if not 0<=y<height:raise ValueError("sprite post outside image")
                                canvas[x*256+y*2:x*256+y*2+2]=bytes((c,1))
                            off+=length+4
                    cached[n]=load(cursor,canvas,"sprite "+n);cursor+=len(canvas)
                metadata+=struct.pack("<4hIB3x",width,height,left,top,cached[n],flip)
                patch_records.append(dict(type=typ,frame=frame,rotation=rot,lump=n,flip=flip))
    load(0xE0010,metadata,"sprite patches")
    if combat:
        weaponmeta=bytearray()
        for n in ("PISGA0","PISGB0","PISFA0"):
            raw=wad[n];width,height,left,top=struct.unpack_from('<4h',raw)
            if not 0<height<=128:raise ValueError("weapon patch height")
            canvas=bytearray(width*256)
            for x in range(width):
                off=struct.unpack_from('<I',raw,8+x*4)[0]
                while raw[off]!=255:
                    topdelta,length=raw[off],raw[off+1]
                    for y,c in enumerate(raw[off+3:off+3+length],topdelta):
                        if y>=height:raise ValueError("weapon post outside image")
                        canvas[x*256+y*2:x*256+y*2+2]=bytes((c,1))
                    off+=length+4
            load(cursor,canvas,"weapon "+n)
            weaponmeta+=struct.pack('<4hIB3x',width,height,left,top,cursor,0);cursor+=len(canvas)
        load(0x1D0010,weaponmeta,"weapon patches")
    pickups=dict(enabled=pickup_enabled,count=len(pickup_rows),types=pickup_types,kinds=pickup_kinds,
                 things=[dict(x=x,y=y,type=t,kind=pickup_kinds[t],rule=PICKUPS[t][1]) for x,y,angle,t,flags in pickup_rows])
    return dict(count=len(selected),types=types,ranged_kinds=ranged_kinds,patches=patch_records,animated=animated,combat=combat,projectiles=projectiles,pickups=pickups,record_size=layout[0],scope=("ground monsters with native combat and map pickups" if combat else "native sight/chase animation without combat") if animated else "static monsters")


def pack(wad_path, image, memory, out, mapname="E1M1", yaw=None, scene=None):
    wad = Wad(wad_path)
    schema = struct.unpack_from("<38H", image, schema_addresses(image)[0])
    (secsz, secfloor, secceil, secfp, seccp, seclight, sidesz, sidsec, sidtx, sidrow,
     sidtop, sidbot, sidmid, linesz, linev1, linev2, linedx, linedy, linesides, linebbox,
     lineflags, linervalid, subsz, subsec, subnum, subfirst, texsz, texmask, texwidth,
     texheight, segsz, nodesz, bootsz, movesz, inputsz, statesz, doorsz, doorstatesz) = schema
    if (segsz, nodesz, bootsz, movesz, inputsz, statesz, doorsz, doorstatesz) != (18, 28, 78, 16, 6, 24, 32, 8): raise ValueError(f"unexpected SDCC layout: {schema}")
    ranges = []
    def load(addr, raw, label):
        if addr < 0 or addr + len(raw) > len(memory): raise ValueError("DDR overflow")
        for lo, hi, previous in ranges:
            if addr < hi and lo < addr + len(raw): raise ValueError(f"overlap: {previous}, {label}")
        memory[addr:addr+len(raw)] = raw
        ranges.append((addr, addr + len(raw), label))
        return addr
    for table in json.loads((out / "tables.json").read_text()):
        load(table["address"], bytes.fromhex(table["hex"]) if "hex" in table else (out / (table["name"] + ".bin")).read_bytes(), table["name"])
    load(0x170010, wad["COLORMAP"][:256*34], "colormap")
    load(0x180010, wad["PLAYPAL"][:768], "palette")
    mi = next(i for i, (n, _) in enumerate(wad.lumps) if n == mapname)
    lump = {n: raw for n, raw in wad.lumps[mi+1:mi+11]}
    vertices = fields(lump["VERTEXES"], "<hh")
    lines = fields(lump["LINEDEFS"], "<7H")
    # Explicit initial demonstration edits only. Never called after CPU boot.
    if scene is not None:
        if not isinstance(scene,dict) or set(scene)-{'line_specials','add_things','line_tags','sector_tags','side_textures'}:raise ValueError('invalid initial scene')
        if image[0xFFF0:0xFFF4]!=b'D805' or image[0xFFF4]<7:raise ValueError('initial scenes require format 7')
        for index,special in scene.get('line_specials',{}).items():
            index=int(index)
            if not 0<=index<len(lines) or special not in MANUAL_DOORS and not (image[0xFFF4]>=8 and special in TAGGED_SWITCHES) and not (image[0xFFF4]>=9 and special in EXIT_SWITCHES):raise ValueError('invalid scene door special')
            row=list(lines[index]);row[3]=special;lines[index]=tuple(row)
        for row in scene.get('add_things',[]):
            if len(row)!=5 or row[3] not in PICKUPS:raise ValueError('invalid scene pickup')
            lump['THINGS']+=struct.pack('<hhHHH',*row)
    sides = fields(lump["SIDEDEFS"], "<hh8s8s8sH")
    sectors = fields(lump["SECTORS"], "<hh8s8shhh")
    if scene:
        if any(scene.get(k) for k in ('line_tags','sector_tags','side_textures')) and image[0xFFF4]<8:raise ValueError('switch scene edits require format 8')
        for key,rows,field in (('line_tags',lines,4),('sector_tags',sectors,6)):
            for index,tag in scene.get(key,{}).items():
                index=int(index)
                if not 0<=index<len(rows) or not isinstance(tag,int) or not 0<=tag<32768:raise ValueError('invalid scene tag')
                row=list(rows[index]);row[field]=tag;rows[index]=tuple(row)
        for index,changes in scene.get('side_textures',{}).items():
            index=int(index)
            if not 0<=index<len(sides) or set(changes)-{'top','bottom','middle'}:raise ValueError('invalid scene texture side')
            row=list(sides[index])
            for field,n in changes.items():
                if not isinstance(n,str) or not 1<=len(n)<=8:raise ValueError('invalid scene texture')
                row[{'top':2,'bottom':3,'middle':4}[field]]=n.upper().encode('ascii').ljust(8,b'\0')
            sides[index]=tuple(row)
    if len(sectors) > 255: raise ValueError("Doom8088 supports at most 255 sectors")
    used = {name(t) for side in sides for t in side[2:5]} - {"-"}
    # Original TEXTURE1 directory and PNAMES; compose assets, not visible columns.
    pnames = wad["PNAMES"]
    patchnames = [name(pnames[4+i*8:12+i*8]) for i in range(struct.unpack_from("<I", pnames)[0])]
    texture_defs = {}
    for texlump in ("TEXTURE1", "TEXTURE2"):
        if texlump not in wad.lookup: continue
        raw = wad[texlump]
        for (offset,) in fields(raw[4:4+4*struct.unpack_from("<I",raw)[0]], "<I"):
            n, _, width, height, _, npatch = struct.unpack_from("<8sIhhIh", raw, offset)
            texture_defs[name(n)] = (width, height, fields(raw[offset+22:offset+22+npatch*10], "<hhhhh"))
    switches_enabled=image[0xFFF0:0xFFF4]==b'D805' and image[0xFFF4]>=8
    if switches_enabled:
        used|={'SW2'+n[3:] for n in used if n.startswith('SW1') and 'SW2'+n[3:] in texture_defs}
    texnames = ["-"] + sorted(used)
    texnums = {n: i for i,n in enumerate(texnames)}
    metadata, pixels, heights = bytearray(texsz * len(texnames)), [], []
    cursor = 0x200010
    for i, n in enumerate(texnames):
        width, height, patches = texture_defs[n] if n != "-" else (1,128,[])
        if height > 128 or width > 256 or width < 1: raise ValueError(f"unsupported texture dimensions: {n} {width}x{height}")
        # Every generic object stays within one 64 KiB page, including textures.
        size = width * 128
        if (cursor & 65535) + size > 65536: cursor = ((cursor + 65535) & ~65535) + 16
        if cursor + size > 0x400000: raise ValueError("texture pointer heap exhausted")
        canvas = bytearray(size)
        for ox, oy, patchnum, _, _ in patches:
            patch = wad[patchnames[patchnum]]
            pw, ph = struct.unpack_from("<hh", patch)
            for x in range(pw):
                destx = x + ox
                if not 0 <= destx < width: continue
                off = struct.unpack_from("<I", patch, 8+4*x)[0]
                previous = -1
                while patch[off] != 255:
                    top, length = patch[off], patch[off+1]
                    if top <= previous: top += previous
                    previous = top
                    for y, value in enumerate(patch[off+3:off+3+length], top+oy):
                        if 0 <= y < height: canvas[destx*128+y] = value
                    off += length + 4
        # Mode Y's original renderer wraps 128-pixel columns; repeat short tiles.
        if height < 128:
            for x in range(width):
                for y in range(height,128): canvas[x*128+y] = canvas[x*128+y%height]
        pixels.append(load(cursor,canvas,"texture " + n)); cursor += size
        heights.append(height)
        struct.pack_into("<H", metadata, i*texsz+texmask, (1 << (width.bit_length()-1))-1)
        struct.pack_into("<h", metadata, i*texsz+texwidth, width)
        struct.pack_into("<h", metadata, i*texsz+texheight, height)
    load(0x100010,metadata,"texture metadata")
    load(0x110010,b"".join(struct.pack("<I",p) for p in pixels),"texture pointers")
    load(0x120010,struct.pack("<"+"h"*len(heights),*heights),"texture heights")
    load(0x130010,struct.pack("<"+"h"*len(heights),*range(len(heights))),"texture translations")
    secbase, sidebase, linebase, segbase, subbase, nodebase = [(i << 16) + 16 for i in range(2,8)]
    def ptr(buf, off, addr): buf[off:off+3] = addr.to_bytes(3,"little")
    def put(buf,off,val,size=2): buf[off:off+size] = (val & ((1 << (size*8))-1)).to_bytes(size,"little")
    secdata = bytearray(len(sectors)*secsz)
    flatnames=sorted(({name(s[2]) for s in sectors}|{name(s[3]) for s in sectors})-{"F_SKY1"})
    flatnums={n:i for i,n in enumerate(flatnames)}
    if image[0xFFF4]>=10:
        for i,n in enumerate(flatnames):
            if n=='F_SKY1':continue
            if len(wad[n])!=4096:raise ValueError('invalid flat '+n)
            load(0x800010+i*4096,wad[n],'flat '+n)
        load(0x140010,b''.join(struct.pack('<I',0x800010+i*4096) for i in range(len(flatnames))),'flat directory')
        # The original SKY1 texture is a cylindrical, column-major texture.
        width,height,patches=texture_defs['SKY1'];sky=bytearray(256*128)
        for ox,oy,pid,_,_ in patches:
            raw=wad[patchnames[pid]];pw,ph=struct.unpack_from('<hh',raw)
            for x in range(pw):
                off=struct.unpack_from('<I',raw,8+x*4)[0]
                while raw[off]!=255:
                    top,length=raw[off:off+2]
                    for y,c in enumerate(raw[off+3:off+3+length],top+oy):
                        if 0<=x+ox<256 and 0<=y<128:sky[(x+ox)*128+y]=c
                    off+=length+4
        load(0x160010,sky,'SKY1 pixels')
    def flat_color(n):
        if name(n) == "F_SKY1": return -2
        if image[0xFFF4]>=10:return flatnums[name(n)]
        raw = wad[name(n)]
        # Most common flat index, as a deterministic approximation of its colour.
        return max(set(raw),key=raw.count)
    for i,(floor,ceil,fp,cp,light,_,_) in enumerate(sectors):
        off = i*secsz
        for field,val,size in ((secfloor,floor<<16,4),(secceil,ceil<<16,4),(secfp,flat_color(fp),2),(seccp,flat_color(cp),2),(seclight,light,2)):
            put(secdata,off+field,val,size)
    load(secbase,secdata,"sectors")
    sidedata = bytearray(len(sides)*sidesz)
    for i,(tx,row,top,bot,mid,sec) in enumerate(sides):
        off=i*sidesz; ptr(sidedata,off+sidsec,secbase+sec*secsz)
        for field,val in ((sidtx,tx),(sidrow,row),(sidtop,texnums.get(name(top),0)),(sidbot,texnums.get(name(bot),0)),(sidmid,texnums.get(name(mid),0))): put(sidedata,off+field,val)
    load(sidebase,sidedata,"sides")
    linedata = bytearray(len(lines)*linesz)
    for i,(v1,v2,flags,_,_,front,back) in enumerate(lines):
        off=i*linesz; (x1,y1),(x2,y2)=vertices[v1],vertices[v2]
        for field,val in ((linev1,x1),(linev1+2,y1),(linev2,x2),(linev2+2,y2),(linedx,x2-x1),(linedy,y2-y1),(linesides,front),(linesides+2,back)):
            put(linedata,off+field,val)
        for j,val in enumerate((max(y1,y2),min(y1,y2),min(x1,x2),max(x1,x2))): put(linedata,off+linebbox+j*2,val)
        put(linedata,off+lineflags,flags,1)
    load(linebase,linedata,"lines")
    segs = fields(lump["SEGS"],"<6H"); segdata=bytearray()
    for v1,v2,angle,linenum,side,offset in segs:
        line=lines[linenum]; sidenum=line[5+side]
        back=line[5+(side^1)]
        frontsec=sides[sidenum][5]; backsec=sides[back][5] if line[2]&4 and back!=65535 else 255
        segdata += struct.pack("<4h4H2B",*vertices[v1],*vertices[v2],offset,(angle+0x4000)&65535,sidenum,linenum,frontsec,backsec)
    load(segbase,segdata,"segs")
    subs=fields(lump["SSECTORS"],"<HH"); subdata=bytearray(len(subs)*subsz)
    for i,(count,first) in enumerate(subs):
        sec=sides[lines[segs[first][3]][5+segs[first][4]]][5]
        ptr(subdata,i*subsz+subsec,secbase+sec*secsz); put(subdata,i*subsz+subnum,count); put(subdata,i*subsz+subfirst,first)
    load(subbase,subdata,"subsectors")
    load(nodebase,lump["NODES"],"BSP nodes")
    # Static collision profiles and the original BLOCKMAP are asset data.
    # They do not contain host-computed player movement or visibility.
    if not 0<len(lines)<=(2048 if image[0xFFF4]>=10 else 512): raise ValueError("motion line limit exceeded")
    xs=[v[0] for v in vertices];ys=[v[1] for v in vertices]
    if min(xs+ys)<-16000 or max(xs+ys)>16000 or max(xs)-min(xs)>16384 or max(ys)-min(ys)>16384:
        raise ValueError("map exceeds bounded int32 collision geometry")
    # Key requirements belong to each use line, even for a shared door sector.
    door_specials=MANUAL_DOORS if image[0xFFF0:0xFFF4]==b'D805' and image[0xFFF4]>=7 else {k:MANUAL_DOORS[k] for k in (1,31)}
    switchrows=[]
    if switches_enabled:
        for i,line in enumerate(lines):
            if image[0xFFF4]>=9 and line[3] in EXIT_SWITCHES:
                switchrows.append((i,[]));continue
            if line[3] not in TAGGED_SWITCHES or not line[4]:continue
            targets=[j for j,sector in enumerate(sectors) if sector[6]==line[4]]
            if targets:switchrows.append((i,targets))
        if len(switchrows)>15:raise ValueError('too many standalone switches')
    doorsectors=sorted({sides[line[6]][5] for line in lines if line[3] in door_specials and line[2]&4 and line[6]!=65535}|{s for _,targets in switchrows for s in targets})
    if len(doorsectors)>(32 if image[0xFFF4]>=10 else 16):raise ValueError("too many standalone doors")
    doorids={sector:i for i,sector in enumerate(doorsectors)}
    doorlinks=[];doordefs=bytearray();doormeta=[]
    for sector in doorsectors:
        ids=[];neighbors=[];points=[]
        for i,line in enumerate(lines):
            a,b,flags,special,tag,front,back=line
            fs=sides[front][5];bs=sides[back][5] if back!=65535 and flags&4 else None
            if fs==sector or bs==sector:points.extend((vertices[a],vertices[b]))
            if bs is not None and sector in (fs,bs):ids.append(i);neighbors.append(bs if fs==sector else fs)
        closed=sectors[sector][1];top=min(sectors[n][1] for n in neighbors)-4
        if top<closed:raise ValueError("invalid door opening range")
        first=len(doorlinks);doorlinks.extend(ids)
        bbox=(min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points))
        doordefs+=struct.pack("<HhhHH4h14x",sector,closed,top,first,len(ids),*bbox)
        doormeta.append(dict(sector=sector,closed=closed,top=top,lines=ids,bbox=bbox))
    doorbase,doorlinkbase=0xA0010,0xA2010
    switchbase=0xA4010
    switchdefs=bytearray();switchmeta=[];switchtokens={}
    extended=image[0xFFF4]>=10
    actions=[0]*256
    def action_token(descriptor,preferred):
        if not extended:return preferred
        if actions[preferred] not in (0,descriptor):
            preferred=next((i for i in range(1,256) if actions[i] in (0,descriptor)),None)
        if preferred is None:raise ValueError('too many distinct use actions')
        actions[preferred]=descriptor
        return preferred
    for number,(index,targets) in enumerate(switchrows):
        line=lines[index];kind=EXIT_SWITCHES.get(line[3],0)
        stay,repeat=TAGGED_SWITCHES.get(line[3],(False,False))
        mask=sum(1<<doorids[s] for s in targets)
        texaddr=off=on=0
        for field,offset in ((2,sidtop),(3,sidbot),(4,sidmid)):
            n=name(sides[line[5]][field]);paired='SW2'+n[3:]
            if n.startswith('SW1') and paired in texnums:
                texaddr=sidebase+line[5]*sidesz+offset;off=texnums[n];on=texnums[paired];break
        switchdefs+=struct.pack('<IHIhhH',mask,index,texaddr,off,on,kind) if extended else struct.pack('<HHIhhH2x',mask,index,texaddr,off,on,kind)
        switchtokens[index]=action_token((number+1)|512|(int(repeat)<<10)|(int(stay)<<8),(17+number)|(int(repeat)<<5)|(int(stay)<<7))
        switchmeta.append(dict(line=index,tag=line[4],targets=targets,mask=mask,texture=texaddr,off=off,on=on,stay=stay,repeat=repeat,kind=kind))
    if switches_enabled:load(switchbase,struct.pack('<H14x',len(switchrows))+switchdefs,'switch definitions')
    doorheader=struct.pack("<HHIII",len(doorsectors),len(doorlinks),doorlinkbase,switchbase if switches_enabled else 0,0xA6010 if extended else 0)
    load(doorbase,doorheader+doordefs,"door definitions")
    load(doorlinkbase,struct.pack("<"+"H"*len(doorlinks),*doorlinks),"door links")
    profiles=bytearray()
    for v1,v2,flags,special,_,front,back in lines:
        solid=not(flags&4) or back==65535 or bool(flags&1)
        fs=sides[front][5];bs=sides[back][5] if back!=65535 and flags&4 else 255
        collisionflags=int(solid)
        if solid: bottom,top=0,0
        else:
            a,b=sectors[sides[front][5]],sectors[sides[back][5]]
            bottom,top=max(a[0],b[0]),min(a[1],b[1])
            if a[:2]!=b[:2] or fs in doorids or bs in doorids:collisionflags|=2
        if vertices[v1]==vertices[v2]: collisionflags=0;bottom,top=-32768,32767
        token=(doorids[bs]+1)|(int(door_specials[special][1])<<7)|(door_specials[special][0]<<5) if special in door_specials and bs in doorids else 0
        if token and extended:
            descriptor=(doorids[bs]+1)|(int(door_specials[special][1])<<8)|(door_specials[special][0]<<6)
            token=action_token(descriptor,token)
        token=switchtokens.get(len(profiles)//16,token)
        profiles+=struct.pack("<6h4B",*vertices[v1],*vertices[v2],bottom,top,collisionflags,fs,bs,token)
    if extended:load(0xA6010,struct.pack("<256H",*actions),"use action table")
    blockraw=lump["BLOCKMAP"]
    if len(blockraw)<8 or len(blockraw)%2 or len(blockraw)>65520: raise ValueError("invalid BLOCKMAP size")
    words=struct.unpack("<"+"H"*(len(blockraw)//2),blockraw)
    cells=words[2]*words[3]
    if not words[2] or not words[3] or 4+cells>len(words): raise ValueError("invalid BLOCKMAP dimensions")
    for offset in set(words[4:4+cells]):
        if offset<4+cells or offset>=len(words) or words[offset]!=0: raise ValueError("invalid BLOCKMAP list")
        cursor=offset+1
        while cursor<len(words) and words[cursor]!=65535:
            if words[cursor]>=len(lines) or cursor-offset>len(lines): raise ValueError("invalid BLOCKMAP linedef")
            cursor+=1
        if cursor==len(words): raise ValueError("unterminated BLOCKMAP list")
    # Static portals with identical floor/ceiling profiles cannot block this
    # controller. Filter those IDs offline, retaining original IDs and sharing
    # duplicate cell lists. The all-lines oracle still checks the native pose.
    filtered=list(words[:4])+[0]*cells
    shared={}
    for cell,offset in enumerate(words[4:4+cells]):
        ids=[];cursor=offset+1
        while words[cursor]!=65535:
            if profiles[words[cursor]*16+12]&3:ids.append(words[cursor])
            cursor+=1
        key=tuple(ids)
        if key not in shared:
            shared[key]=len(filtered);filtered.extend((0,*ids,65535))
        filtered[4+cell]=shared[key]
    filteredraw=struct.pack("<"+"H"*len(filtered),*filtered)
    if len(filteredraw)>65520:raise ValueError("filtered BLOCKMAP exceeds one bank")
    collisionbase,blockbase=0x80010,0x90010
    load(collisionbase,profiles,"static collision profiles")
    load(blockbase,filteredraw,"static collision BLOCKMAP")
    monsters=pack_monsters(wad,lump["THINGS"],image,load) if struct.unpack_from("<2H",image,schema_addresses(image)[1]) in ((12,16),(20,16)) else None
    player=next(t for t in fields(lump["THINGS"],"<hhHHH") if t[3]==1)
    x,y,angle,_,_=player
    if yaw is not None: angle=yaw
    # Locate the player's sector through the raw WAD BSP, only for view height.
    node=len(lump["NODES"])//28-1
    while not node&0x8000:
        nx,ny,dx,dy=struct.unpack_from("<4h",lump["NODES"],node*28)
        side=0 if (x-nx)*dy - (y-ny)*dx <= 0 else 1
        node=struct.unpack_from("<H",lump["NODES"],node*28+24+2*side)[0]
    first=subs[node&0x7FFF][1]; psec=sides[lines[segs[first][3]][5+segs[first][4]]][5]
    boot=struct.pack("<11I3h2iIi",segbase,secbase,subbase,linebase,sidebase,nodebase,0x100010,0x110010,0x120010,0x130010,0x180010,
                     len(lump["NODES"])//28,len(sectors),len(lines),x<<16,y<<16,int(angle*(1<<32)//360)&0xFFFFFFFF,(sectors[psec][0]+41)<<16)
    boot+=struct.pack("<3I",collisionbase,blockbase,doorbase)
    result=dict(monsters=monsters,doors=doormeta,flats=flatnames,motion=dict(lines=len(lines),blockmap_cells=cells,blockmap_bytes=len(filteredraw),original_blockmap_bytes=len(blockraw)),map=mapname,wad_sha256=hashlib.sha256(wad.raw).hexdigest(),schema=schema,textures=len(texnames),player=[x,y,angle],sectors=len(sectors),lines=len(lines),segs=len(segs),nodes=len(lump["NODES"])//28,preloaded_bytes=sum(hi-lo for lo,hi,_ in ranges))
    if scene is not None:result['scene']=scene
    if switches_enabled:result['switches']=switchmeta
    (out/"assets.json").write_text(json.dumps(result,indent=2))
    return boot,result


def load_native(directory,image,memory):
    """Load a validated translated scene before CPU boot, without the IWAD."""
    import zipfile
    directory=Path(directory)
    assets=json.loads((directory/'assets.json').read_text())
    with zipfile.ZipFile(directory/'ddr.zip') as archive:
        info=json.loads(archive.read('memory.json'))
        if info['capacity']!=len(memory):raise ValueError('translated DDR capacity mismatch')
        if info['firmware_sha256']!=hashlib.sha256(image).hexdigest():raise ValueError('translated firmware checksum mismatch')
        if info['source_sha256']!=assets['wad_sha256']:raise ValueError('translated source checksum mismatch')
        previous=-4096
        blocks=[]
        for block in info['blocks']:
            address=block['address'];length=block['bytes']
            if address%4096 or length!=4096 or address<=previous or address+length>len(memory):raise ValueError('invalid translated memory block')
            raw=archive.read(f'{address:08x}.bin')
            if len(raw)!=length or hashlib.sha256(raw).hexdigest()!=block['sha256']:raise ValueError('translated block checksum mismatch')
            blocks.append((address,raw));previous=address
        boot=bytes.fromhex(info['boot'])
        if len(boot)!=78:raise ValueError('translated boot size mismatch')
        # Validation completes before mutating the caller's memory.
        for address,raw in blocks:memory[address:address+len(raw)]=raw
    return boot,assets
