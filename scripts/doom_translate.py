#!/usr/bin/env python3
"""Translate an entire supplied Doom WAD in one reproducible, audited pass.

DPAK version 1 is an indexed archive: all source lumps retained byte-for-byte,
all patch/texture/flat pixels decoded to indexed colour + explicit coverage,
and every classic map normalized with complete original fields. An optional
native firmware folder also produces per-map sparse DDR images and captures.
This is asset translation, not a claim that every original thinker is ported.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil, struct, zipfile
from pathlib import Path
import doom_assets as A

MAP_FORMATS={"THINGS":("<hhHHH",("x","y","angle","type","flags")),
 "LINEDEFS":("<7H",("v1","v2","flags","special","tag","front","back")),
 "SIDEDEFS":("<hh8s8s8sH",("x_offset","y_offset","upper","lower","middle","sector")),
 "VERTEXES":("<hh",("x","y")),"SEGS":("<6H",("v1","v2","angle","line","side","offset")),
 "SSECTORS":("<HH",("count","first")),
 "NODES":("<12h2H",("x","y","dx","dy","right_top","right_bottom","right_left","right_right","left_top","left_bottom","left_left","left_right","right_child","left_child")),
 "SECTORS":("<hh8s8sHHH",("floor","ceiling","floor_flat","ceiling_flat","light","special","tag"))}
MAP_LUMPS=tuple(MAP_FORMATS)+("REJECT","BLOCKMAP")

def digest(data):return hashlib.sha256(data).hexdigest()
def encoded(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()

def patch(raw):
    """Strict Doom column-post decoder, including relative tall-patch posts."""
    if len(raw)<8:raise ValueError('short patch header')
    w,h,left,top=struct.unpack_from('<4h',raw)
    if not 0<w<=4096 or not 0<h<=4096 or 8+w*4>len(raw):raise ValueError('invalid patch dimensions')
    pixels=bytearray(w*h);mask=bytearray(w*h)
    for x in range(w):
        pos=struct.unpack_from('<I',raw,8+4*x)[0]
        if not 8+4*w<=pos<len(raw):raise ValueError('invalid column pointer')
        previous=-1
        while True:
            if pos>=len(raw):raise ValueError('unterminated column')
            y=raw[pos]
            if y==255:break
            if pos+4>len(raw):raise ValueError('short post')
            length=raw[pos+1]
            if pos+length+4>len(raw):raise ValueError('post outside lump')
            if y<=previous:y+=previous
            previous=y
            if y+length>h:raise ValueError('post outside patch height')
            for k,c in enumerate(raw[pos+3:pos+3+length],y):
                pixels[k*w+x]=c;mask[k*w+x]=255
            pos+=length+4
    return dict(width=w,height=h,left=left,top=top),bytes(pixels),bytes(mask)

def texture_definitions(wad):
    pn=wad['PNAMES'];count=struct.unpack_from('<I',pn)[0]
    if len(pn)!=4+count*8:raise ValueError('PNAMES length')
    names=[A.name(pn[4+i*8:12+i*8]) for i in range(count)];definitions={}
    for lumpname in ('TEXTURE1','TEXTURE2'):
        if lumpname not in wad.lookup:continue
        raw=wad[lumpname];count=struct.unpack_from('<I',raw)[0]
        if 4+count*4>len(raw):raise ValueError('texture directory length')
        for (offset,) in A.fields(raw[4:4+count*4],'<I'):
            if offset+22>len(raw):raise ValueError('texture definition outside lump')
            n,flags,w,h,column,npatch=struct.unpack_from('<8sIhhIh',raw,offset)
            if w<=0 or h<=0 or npatch<0 or offset+22+10*npatch>len(raw):raise ValueError('invalid texture definition')
            refs=[]
            for x,y,pid,step,cmap in A.fields(raw[offset+22:offset+22+10*npatch],'<hhhhh'):
                if not 0<=pid<len(names):raise ValueError('patch index outside PNAMES')
                refs.append(dict(name=names[pid],x=x,y=y,step_direction=step,colormap=cmap))
            definitions[A.name(n)]=dict(width=w,height=h,flags=flags,column_directory=column,patches=refs,source=lumpname)
    return names,definitions

def engine_metadata():
    """Preserve the original state graph and thing definitions as data.

    Actions remain symbolic names. Translating a state is not executing an
    original thinker or substituting a Python implementation for one.
    """
    path=Path(__file__).resolve().parents[1]/'fw/doom/vendor/Doom8088/info.c'
    text=path.read_text();states={};things={}
    for sprite,frame,tics,action,nxt,label in re.findall(r'\{SPR_(\w+),(\d+),(-?\d+),(\w+),(S_\w+)\},?\s*//\s*(S_\w+)',text):
        states[label]=dict(sprite=sprite,frame=int(frame)&32767,fullbright=bool(int(frame)&32768),ticks=int(tics),action=action,next=nxt)
    for label,body in re.findall(r'\{\s*//\s*(MT_\w+)\n(.*?)\n\s*\},?',text,re.S):
        fields={key:value.strip().rstrip(',').strip() for value,key in re.findall(r'^\s*(.*?)\s*//\s*(\w+)\s*$',body,re.M)}
        if fields:things[label]=fields
    if not states or not things:raise ValueError('original state metadata not found')
    missing={v['next'] for v in states.values()}-set(states)-{'S_NULL'}
    if missing:raise ValueError('unresolved original state references: '+str(sorted(missing)))
    return dict(source='Doom8088 info.c',source_commit='b3073a2eb2811cd14caba6549694fc3bfcd6dd29',source_sha256=digest(path.read_bytes()),
                states=states,things=things,execution='Data translation only. Original action functions are not implemented by this converter.')


def map_data(wad,index):
    marker=wad.lumps[index][0];raws=dict(wad.lumps[index+1:index+11])
    if set(raws)!=set(MAP_LUMPS):raise ValueError('incomplete classic map '+marker)
    result=dict(name=marker,records={},raw_hashes={k:digest(v) for k,v in raws.items()})
    for name,(fmt,keys) in MAP_FORMATS.items():
        if len(raws[name])%struct.calcsize(fmt):raise ValueError(marker+' malformed '+name)
        result['records'][name]=[dict(zip(keys,(v.decode('ascii').rstrip('\0') if isinstance(v,bytes) else v for v in row))) for row in A.fields(raws[name],fmt)]
    t=result['records'];nv,ns,nl,nsec,nsg,nss,nn=(len(t[k]) for k in ('VERTEXES','SIDEDEFS','LINEDEFS','SECTORS','SEGS','SSECTORS','NODES'))
    for side in t['SIDEDEFS']:
        if side['sector']>=nsec:raise ValueError(marker+' bad side sector')
    for line in t['LINEDEFS']:
        if max(line['v1'],line['v2'])>=nv or line['front']>=ns or line['back']!=65535 and line['back']>=ns:raise ValueError(marker+' bad line reference')
    for seg in t['SEGS']:
        if max(seg['v1'],seg['v2'])>=nv or seg['line']>=nl or seg['side']>1:raise ValueError(marker+' bad seg reference')
        if t['LINEDEFS'][seg['line']][('front','back')[seg['side']]]==65535:raise ValueError(marker+' seg without side')
    for sub in t['SSECTORS']:
        if not sub['count'] or sub['first']+sub['count']>nsg:raise ValueError(marker+' bad subsector')
    # DFS verifies the exact BSP child graph without assuming node ordering.
    active=set();done=set()
    def visit(child):
        if child&0x8000:
            if child&0x7fff>=nss:raise ValueError(marker+' bad BSP leaf')
            return
        if child>=nn or child in active:raise ValueError(marker+' invalid/cyclic BSP')
        if child in done:return
        active.add(child)
        for key in ('right_child','left_child'):visit(t['NODES'][child][key])
        active.remove(child);done.add(child)
    if nn:visit(nn-1)
    if len(raws['REJECT'])*8<nsec*nsec:raise ValueError(marker+' short REJECT matrix')
    block=raws['BLOCKMAP']
    if len(block)<8 or len(block)%2:raise ValueError(marker+' malformed BLOCKMAP')
    ox,oy,w,h=struct.unpack_from('<hhHH',block);words=struct.unpack('<'+'H'*(len(block)//2),block)
    if not w or not h or 4+w*h>len(words):raise ValueError(marker+' bad block dimensions')
    lists={}
    for off in sorted(set(words[4:4+w*h])):
        if not 4+w*h<=off<len(words) or words[off]!=0:raise ValueError(marker+' bad block offset')
        end=off+1
        while end<len(words) and words[end]!=65535:
            if words[end]>=nl:raise ValueError(marker+' bad block line')
            end+=1
        if end==len(words):raise ValueError(marker+' unterminated block list')
        lists[str(off)]=list(words[off+1:end])
    result['blockmap']=dict(origin=[ox,oy],width=w,height=h,cell_offsets=list(words[4:4+w*h]),lists=lists)
    result['reject']=dict(bytes=len(raws['REJECT']),sector_count=nsec,bit_order='LSB first; row-major sector pairs')
    result['counts']={k:len(v) for k,v in t.items()}
    result['thing_types']=dict(sorted(collections.Counter(row['type'] for row in t['THINGS']).items()))
    result['line_specials']=dict(sorted(collections.Counter(row['special'] for row in t['LINEDEFS'] if row['special']).items()))
    result['sector_specials']=dict(sorted(collections.Counter(row['special'] for row in t['SECTORS'] if row['special']).items()))
    supported=set(A.MANUAL_DOORS)|set(A.TAGGED_SWITCHES)|set(A.EXIT_SWITCHES)
    result['native_unsupported_line_specials']={k:v for k,v in result['line_specials'].items() if k not in supported}
    result['native_unsupported_sector_specials']=result['sector_specials']
    result['native_unsupported_thing_types']={k:v for k,v in result['thing_types'].items() if k not in {1,2,3,4,11}|set(A.PICKUPS)|{3001,3004,9,3002,58,3003}}
    return result

def zip_write(archive,path,raw):
    info=zipfile.ZipInfo(path,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
    info.create_system=3;info.external_attr=0o100644<<16
    archive.writestr(info,raw,compresslevel=9)


class Bundle:
    def __init__(self,path):
        self.z=zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9);self.entries=[]
    def add(self,path,raw,role,**meta):
        zip_write(self.z,path,raw);e=dict(path=path,bytes=len(raw),sha256=digest(raw),role=role,**meta);self.entries.append(e);return e
    def close(self,manifest):
        manifest['entries']=self.entries;zip_write(self.z,'manifest.json',encoded(manifest));self.z.close()

def graphics_atlas(graphics,palette,path):
    from PIL import Image,ImageDraw
    columns=8;cellw,cellh=128,148;sheet=Image.new('RGB',(columns*cellw,((len(graphics)+columns-1)//columns)*cellh),(24,24,28));d=ImageDraw.Draw(sheet)
    for i,(n,meta,pix,mask) in enumerate(graphics):
        im=Image.frombytes('P',(meta['width'],meta['height']),pix);im.putpalette(palette);im=im.convert('RGBA');im.putalpha(Image.frombytes('L',im.size,mask));im.thumbnail((120,124),Image.Resampling.NEAREST)
        x=i%columns*cellw+(cellw-im.width)//2;y=i//columns*cellh+4
        sheet.paste(im,(x,y),im);d.text((i%columns*cellw+4,i//columns*cellh+130),n,fill='white')
    sheet.save(path)

def convert(wad_path,out,*,native=None,verify_native=False,frames=4):
    out.mkdir(parents=True,exist_ok=True);wad=A.Wad(wad_path);pnames,definitions=texture_definitions(wad)
    maps=[map_data(wad,i) for i,(n,_) in enumerate(wad.lumps) if re.fullmatch(r'E\dM\d|MAP\d\d',n)]
    metadata=engine_metadata()
    for level in maps:
        for side in level['records']['SIDEDEFS']:
            for key in ('upper','lower','middle'):
                if side[key].upper() not in definitions and side[key]!='-':raise ValueError(level['name']+' unresolved texture '+side[key])
        for sector in level['records']['SECTORS']:
            for key in ('floor_flat','ceiling_flat'):
                if sector[key].upper()!='F_SKY1' and (sector[key].upper() not in wad.lookup or len(wad[sector[key].upper()])!=4096):raise ValueError(level['name']+' unresolved flat '+sector[key])
    if len(wad['PLAYPAL'])%768 or len(wad['COLORMAP'])%256:raise ValueError('invalid palette/colormap length')
    bundle=Bundle(out/'doom-assets.dpak');bundle.add('engine/state-graph.json',encoded(metadata),'original-state-metadata')
    graphics=[];patches={};flat_indices=set();sprites=set();state=None
    for i,(n,raw) in enumerate(wad.lumps):
        if re.fullmatch(r'F\d?_START',n):state='flat'
        if re.fullmatch(r'F\d?_END',n):state=None
        if re.fullmatch(r'S\d?_START',n):state='sprite'
        if re.fullmatch(r'S\d?_END',n):state=None
        if state=='flat' and raw:flat_indices.add(i)
        if state=='sprite' and raw:sprites.add(i)
        bundle.add(f'raw/{i:05d}-{n or "unnamed"}.bin',raw,'source-lump',name=n,index=i)
    patch_count=flat_count=0
    map_indices=set()
    for i,(n,_) in enumerate(wad.lumps):
        if any(n==m['name'] for m in maps):map_indices.update(range(i,i+11))
    # Explicit graphics namespaces plus strict structural detection of menu,
    # status-bar, intermission, title and font patches outside those markers.
    for i,(n,raw) in enumerate(wad.lumps):
        if not raw or i in map_indices:continue
        if i in flat_indices:
            if len(raw)!=4096:raise ValueError('invalid flat '+n)
            meta=dict(width=64,height=64,left=0,top=0);pix=raw;mask=bytes([255])*4096;role='flat';flat_count+=1
        else:
            try:meta,pix,mask=patch(raw)
            except ValueError:
                if n in pnames or i in sprites:raise ValueError('undecodable required patch '+n)
                continue
            role='sprite' if i in sprites else ('texture-patch' if n in pnames else 'interface-patch');patch_count+=1
            patches[n]=(meta,pix,mask)
        base=f'graphics/{i:05d}-{n}'
        bundle.add(base+'.idx',pix,role,name=n,source_index=i,encoding='row-major palette indices',**meta)
        bundle.add(base+'.mask',mask,'coverage',name=n,encoding='row-major 0 or 255',**meta)
        graphics.append((n,meta,pix,mask))
    for n,definition in definitions.items():
        w,h=definition['width'],definition['height'];pixels=bytearray(w*h);mask=bytearray(w*h)
        for ref in definition['patches']:
            meta,src,cov=patches[ref['name']];pw,ph=meta['width'],meta['height']
            for sy in range(ph):
                y=sy+ref['y']
                if not 0<=y<h:continue
                for sx in range(pw):
                    x=sx+ref['x'];si=sy*pw+sx
                    if 0<=x<w and cov[si]:pixels[y*w+x]=src[si];mask[y*w+x]=255
        meta=dict(width=w,height=h,left=0,top=0)
        bundle.add('textures/'+n+'.idx',pixels,'composite-texture',name=n,encoding='row-major palette indices',**definition)
        bundle.add('textures/'+n+'.mask',mask,'coverage',name=n,**meta)
        graphics.append((n,meta,bytes(pixels),bytes(mask)))
    for m in maps:bundle.add('levels/'+m['name']+'.json',encoded(m),'normalized-level',name=m['name'])
    palette=wad['PLAYPAL'][:768];palettes=len(wad['PLAYPAL'])//768
    rotations=collections.defaultdict(list)
    sprite_names={wad.lumps[i][0] for i in sprites}
    for n in patches:
        if n in sprite_names and re.fullmatch(r'[A-Z0-9]{4}[A-Z][0-8]([A-Z][0-8])?',n):
            for off in (4,6):
                if off<len(n):rotations[n[:4]+n[off]].append(dict(lump=n,rotation=int(n[off+1]),flip=off==6))
    manifest=dict(format='DPAK',version=1,source_sha256=digest(wad.raw),source_bytes=len(wad.raw),source_lumps=len(wad.lumps),
                  raw_lumps_preserved=len(wad.lumps),maps=[m['name'] for m in maps],patches=patch_count,flats=flat_count,textures=len(definitions),palettes=palettes,colormap_bytes=len(wad['COLORMAP']),
                  sprite_frames=dict(sorted(rotations.items())),original_states=len(metadata['states']),original_thing_definitions=len(metadata['things']),all_source_lumps_retained=True,
                  native_scope='Standalone native controller/combat and renderer. Original Doom thinkers, complete weapon/inventory rules, sector effects, lifts, teleports, intermission and campaign progression remain unported.')
    bundle.close(manifest)
    # Verify the archived bytes independently of the write loop.
    with zipfile.ZipFile(out/'doom-assets.dpak') as z:
        if z.testzip():raise AssertionError('DPAK CRC verification failed')
        for e in manifest['entries']:
            if digest(z.read(e['path']))!=e['sha256']:raise AssertionError('DPAK content hash mismatch')
    report={k:v for k,v in manifest.items() if k not in ('entries','sprite_frames')}
    report['entries']=len(manifest['entries']);report['decoded_graphics']=len(graphics);report['map_audit']=[]
    graphics_atlas([g for g in graphics if g[0] in definitions],palette,out/'wall-textures.png')
    graphics_atlas([g for g in graphics if g[0] in {wad.lumps[i][0] for i in flat_indices}],palette,out/'floor-ceiling-flats.png')
    graphics_atlas([g for g in graphics if g[0].endswith(('A1','A1A5','A0')) and re.match('POSS|SPOS|TROO|SARG|BOSS|[A-Z]{4}',g[0])],palette,out/'sprite-graphics.png')
    for m in maps:
        audit={k:m[k] for k in ('name','counts','thing_types','line_specials','sector_specials','native_unsupported_line_specials','native_unsupported_sector_specials','native_unsupported_thing_types')}
        if native:
            import doom_sim as S
            dest=out/'native'/m['name'];dest.mkdir(parents=True,exist_ok=True)
            # Each scene is a sparse memory image. Every loaded byte and its
            # address are retained; zero memory does not bloat nine 32MB files.
            memory=bytearray(32*1024*1024);image=(native/'doom_renderer.bin').read_bytes()
            for f in ('tables.json','cache-config.json'):shutil.copy2(native/f,dest/f)
            boot,assets=A.pack(wad_path,image,memory,dest,mapname=m['name'])
            blocks=[]
            with zipfile.ZipFile(dest/'ddr.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
                for addr in range(0,len(memory),4096):
                    raw=memory[addr:addr+4096]
                    if any(raw):zip_write(z,f'{addr:08x}.bin',raw);blocks.append(dict(address=addr,bytes=len(raw),sha256=digest(raw)))
                zip_write(z,'memory.json',encoded(dict(capacity=len(memory),boot=boot.hex(),blocks=blocks,source_sha256=digest(wad.raw),firmware_sha256=digest(image))))
            audit['native_pack']='passed';audit['native_assets']=assets
            if verify_native:
                import doom_renderer as R
                for f in ('doom_renderer.bin','doom_renderer.ihx','banking.json'):shutil.copy2(native/f,dest/f)
                results,_=R.simulate(None,dest,packed=dest,frames=frames,commands=[dict(turn=512) for _ in range(frames)],latency=64,save_frames=True)
                audit['native_verification']={k:results[k] for k in ('stack_wraps','stack_high','ddr','palette_verified','frames','bank_switches')}
                print(m['name']+' native verified',flush=True)
        report['map_audit'].append(audit)
    (out/'translation-report.json').write_bytes(encoded(report))
    lines=['# Complete supplied-WAD translation','',f"Source SHA-256: `{report['source_sha256']}`",'',f"Preserved {report['source_lumps']} of {report['source_lumps']} original lumps; decoded {patch_count} patches, {flat_count} flats and {len(definitions)} composite textures. All {palettes} palettes and all COLORMAP bytes are retained.",'',
           'DPAK is a ZIP-compatible indexed asset bundle. Every payload has a SHA-256 entry in manifest.json. Indexed pixels and coverage masks retain transparent posts, patch origins, frame rotations and mirroring. Raw sound/music/interface data and all map lumps remain byte-exact. Normalized levels retain every original field, special, tag and thing flag. The original Doom8088 state graph, frame brightness, frame durations, symbolic actions and thing definitions are translated as metadata. BSP, sidedef, linedef, subsector, blockmap and REJECT references are validated.','',
           '| Map | Lines | Sectors | Segs | Native pack | Native capture |','|---|---:|---:|---:|---|---|']
    for m in report['map_audit']:
        c=m['counts'];lines.append(f"| {m['name']} | {c['LINEDEFS']} | {c['SECTORS']} | {c['SEGS']} | {m.get('native_pack','not requested')} | {'passed' if 'native_verification' in m else 'not requested'} |")
    lines+=['','## Runtime boundary','',manifest['native_scope'],'','Translated assets are complete for this supplied WAD. The supplied shareware WAD contains E1M1 through E1M9, not the registered episodes or Doom II. Unsupported native line/sector specials and thing types are listed per level in translation-report.json, with original data retained in the bundle. Conversion does not turn an unported action into a working game mechanic.','',
            '## Reproduce','',f'`python3 scripts/doom_translate.py --wad /path/to/doom1.wad --native /path/to/built-firmware --verify-native --out /path/to/output`','']
    (out/'README.md').write_text('\n'.join(lines))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wad',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--native',type=Path);p.add_argument('--verify-native',action='store_true');p.add_argument('--frames',type=int,default=4)
    a=p.parse_args()
    if a.verify_native and not a.native:p.error('--verify-native requires --native')
    r=convert(a.wad,a.out,native=a.native,verify_native=a.verify_native,frames=a.frames)
    print(json.dumps({k:r[k] for k in ('source_lumps','patches','flats','textures','maps','decoded_graphics','entries')},indent=2))
if __name__=='__main__':main()
