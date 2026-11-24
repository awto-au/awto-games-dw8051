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

def pack_monsters(wad, raw_things, image, load):
    """Convert original map things and transparent patches, never visibility."""
    layout=struct.unpack_from("<2H",image,schema_addresses(image)[1])
    combat=image[0xFFF0:0xFFF4]==b"D805"
    if layout not in ((12,16),(20,16)):
        raise ValueError("unexpected native sprite layout")
    projectiles=combat and image[0xFFF4]>=5
    selected=[t for t in fields(raw_things,"<hhHHH") if t[3] in MONSTERS and t[4]&2 and not t[4]&16]
    if len(selected)>128: raise ValueError("static sprite limit is 128 map things")
    types=sorted({t[3] for t in selected})
    kinds={t:i for i,t in enumerate(types)}
    animated=layout[0]==20
    records=b"".join(struct.pack("<hhHHi",x,y,(angle*65536//360)&65535,kinds[t],0)+
                     ((bytes(6)+struct.pack("<H",60 if t==3001 else 20)) if combat else bytes(8))
                     if animated else struct.pack("<hhHHi",x,y,(angle*65536//360)&65535,kinds[t],0)
                     for x,y,angle,t,_ in selected)
    ranged_kinds=sum(1<<kinds[t] for t in types if t in (3004,9)) if combat and image[0xFFF4]>=4 else 0
    header=struct.pack("<3H10x",len(selected),len(selected)+(8 if projectiles else 0),len(types)) if projectiles else struct.pack("<HH12x",len(selected),ranged_kinds)
    load(0xD0010,header+records+(bytes(160) if projectiles else b""),"monster things")
    if projectiles:
        load(0xD3010,b''.join(struct.pack('<H',int(t==3001)) for t in types),"monster attack kinds")
        load(0xD6010,bytes(128),"projectile states")
    metadata=bytearray();cursor=0x400010;cached={};patch_records=[]
    for typ in types+([0] if projectiles else []):
        prefix=MONSTERS[typ] if typ else "BAL1"
        frame_set=("ABCDEFHIJKLM" if typ==3001 else "ABCDEFGHIJKL") if combat else ("ABCD" if animated else "A")
        if not typ:frame_set="ABCDEEEEEEEE"
        if combat and typ and typ not in (3001,3004,9):raise ValueError("combat prototype supports imps and soldiers")
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
    return dict(count=len(selected),types=types,ranged_kinds=ranged_kinds,patches=patch_records,animated=animated,combat=combat,projectiles=projectiles,record_size=layout[0],scope=("ground monsters with native sight/chase, pistol damage and contact combat" if combat else "native sight/chase animation without combat") if animated else "static monsters")


def pack(wad_path, image, memory, out, mapname="E1M1", yaw=None):
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
    sides = fields(lump["SIDEDEFS"], "<hh8s8s8sH")
    sectors = fields(lump["SECTORS"], "<hh8s8shhh")
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
    def flat_color(n):
        if name(n) == "F_SKY1": return -2
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
    if not 0<len(lines)<=512: raise ValueError("motion supports 1..512 lines")
    xs=[v[0] for v in vertices];ys=[v[1] for v in vertices]
    if min(xs+ys)<-16000 or max(xs+ys)>16000 or max(xs)-min(xs)>16384 or max(ys)-min(ys)>16384:
        raise ValueError("map exceeds bounded int32 collision geometry")
    # Unlocked manual raise/wait/close (1), raise/stay (31), grouped by
    # their back-side target sector. Other specials and keys remain unsupported.
    doorsectors=sorted({sides[line[6]][5] for line in lines if line[3] in (1,31) and line[2]&4 and line[6]!=65535})
    if len(doorsectors)>16:raise ValueError("too many standalone doors")
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
    doorheader=struct.pack("<HHI8x",len(doorsectors),len(doorlinks),doorlinkbase)
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
        token=doorids[bs]+1+(128 if special==31 else 0) if special in (1,31) and bs in doorids else 0
        profiles+=struct.pack("<6h4B",*vertices[v1],*vertices[v2],bottom,top,collisionflags,fs,bs,token)
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
    result=dict(monsters=monsters,doors=doormeta,motion=dict(lines=len(lines),blockmap_cells=cells,blockmap_bytes=len(filteredraw),original_blockmap_bytes=len(blockraw)),map=mapname,wad_sha256=hashlib.sha256(wad.raw).hexdigest(),schema=schema,textures=len(texnames),player=[x,y,angle],sectors=len(sectors),lines=len(lines),segs=len(segs),nodes=len(lump["NODES"])//28,preloaded_bytes=sum(hi-lo for lo,hi,_ in ranges))
    (out/"assets.json").write_text(json.dumps(result,indent=2))
    return boot,result
