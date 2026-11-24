"""Whole-WAD conversion, exact retained data, bounds and native graphics oracles."""
import json,os,struct,sys,zipfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import doom_assets as A,doom_translate as T,doom_renderer as R,doom_sim as S,ddr_sim as D,fastmachine as F
from test_doom_platform import build_platform


def test_patch_zero_is_opaque_and_transparent_posts_remain_separate():
    raw=struct.pack('<4hI',1,4,-3,7,12)+bytes((1,2,0,0,25,0,255))
    meta,pixels,mask=T.patch(raw)
    assert meta==dict(width=1,height=4,left=-3,top=7)
    assert pixels==bytes((0,0,25,0)) and mask==bytes((0,255,255,0))
    for damaged in (raw[:10],raw[:-1],raw[:12]+bytes((3,2,0,0,25,0,255))):
        with pytest.raises(ValueError):T.patch(damaged)


def test_relative_tall_patch_posts_and_mirrored_metadata():
    raw=struct.pack('<4hI',1,300,0,0,12)+bytes((250,1,0,4,0,5,1,0,9,0,255))
    meta,pixels,mask=T.patch(raw)
    assert meta['height']==300 and pixels[250]==4 and pixels[255]==9
    assert sum(c!=0 for c in mask)==2


@pytest.fixture(scope='module')
def translated(tmp_path_factory):
    path=os.environ.get('AWTO_DOOM_WAD')
    if not path:pytest.skip('set AWTO_DOOM_WAD')
    out=tmp_path_factory.mktemp('translated');report=T.convert(Path(path),out)
    return Path(path),out,report


def test_every_source_lump_and_normalized_record_roundtrips(translated):
    path,out,report=translated;wad=A.Wad(path)
    assert report['source_lumps']==report['raw_lumps_preserved']==len(wad.lumps)
    assert report['maps']==[f'E1M{i}' for i in range(1,10)]
    with zipfile.ZipFile(out/'doom-assets.dpak') as z:
        manifest=json.loads(z.read('manifest.json'))
        for e in manifest['entries']:
            data=z.read(e['path']);assert len(data)==e['bytes'] and T.digest(data)==e['sha256']
        for i,(name,raw) in enumerate(wad.lumps):assert z.read(f'raw/{i:05d}-{name or "unnamed"}.bin')==raw
        for mapname in report['maps']:
            data=json.loads(z.read('levels/'+mapname+'.json'));index=next(i for i,(n,_) in enumerate(wad.lumps) if n==mapname);lumps=dict(wad.lumps[index+1:index+11])
            for name,(fmt,keys) in T.MAP_FORMATS.items():
                rows=data['records'][name]
                packed=b''.join(struct.pack(fmt,*(row[k].encode().ljust(8,b'\0') if isinstance(row[k],str) else row[k] for k in keys)) for row in rows)
                assert packed==lumps[name]
            assert data['raw_hashes']=={n:T.digest(raw) for n,raw in lumps.items()}
        assert report['patches']==968 and report['flats']==54 and report['textures']==125
        assert report['decoded_graphics']==1147


def test_original_patch_pixels_match_an_independent_post_walk(translated):
    path,out,_=translated;wad=A.Wad(path)
    with zipfile.ZipFile(out/'doom-assets.dpak') as z:
        m=json.loads(z.read('manifest.json'))
        entries={e['name']:e for e in m['entries'] if e['role'] in ('sprite','interface-patch','texture-patch')}
        for name in ('BOSSA1','SARGA1','STBAR','TITLEPIC','PISGA0'):
            e=entries[name];raw=wad[name];pixels=z.read(e['path']);mask=z.read(e['path'].replace('.idx','.mask'));w,h,_,_=struct.unpack_from('<4h',raw)
            expected={}
            for x in range(w):
                off=struct.unpack_from('<I',raw,8+x*4)[0]
                while raw[off]!=255:
                    top,length=raw[off:off+2]
                    for y,c in enumerate(raw[off+3:off+3+length],top):expected[(x,y)]=c
                    off+=length+4
            for y in range(h):
                for x in range(w):
                    assert bool(mask[y*w+x])==((x,y) in expected)
                    if (x,y) in expected:assert pixels[y*w+x]==expected[x,y]
        assert m['sprite_frames']['BOSSA'] and m['sprite_frames']['SARGA']


@pytest.fixture(scope='module')
def graphics_image(tmp_path_factory):
    out=tmp_path_factory.mktemp('native-planes');build_platform(out,True,ROOT/'tests/doom_graphics_fw.c',(ROOT/'fw/doom/planes.c',))
    return S.load_ihx(out/'platform.ihx')


def trunc(a,b):return (abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)


@pytest.mark.parametrize('sky',[False,True])
def test_native_plane_and_sky_pixels_match_fixed_point_oracle(graphics_image,sky):
    c=F.Core(graphics_image);c.set_dw(json.loads(F.MODEL_JSON.read_text()));c.reset();c.set_xpage_sfr(0x92);c.set_ddr(D.config(),latency_clk=64)
    try:
        ram=c.ddr_mem();flat=bytes((x*3+y*7)&255 for y in range(64) for x in range(64));ram[0x800010:0x801010]=flat
        ram[0x140010:0x140014]=struct.pack('<I',0x800010)
        palette=bytes((i^0x55) for i in range(256));ram[0x170010+7*256:0x170110+7*256]=palette
        skydata=bytes((x+y*5)&255 for x in range(256) for y in range(128));ram[0x160010:0x168010]=skydata
        for _ in range(10):
            c.run(10000)
            if c.xram[0xF600]==0xA5:break
        for x,y,cos,sin,height,z,col in ((17,-23,65536,0,0,41,7),(-101,62,0,65536,128,41,44),(0,0,-65536,0,-64,41,59)):
            angle=0xFEDCBA98;first,last=0,127
            c.xram[0xF300:0xF324]=struct.pack('<6iIhh4B',x*65536,y*65536,z*65536,cos,sin,height*65536,angle,0,132,col,first,last,int(sky))
            c.xram[0xF620]=1
            for _ in range(100):
                c.run(10000)
                if not c.xram[0xF620]:break
            else:pytest.fail('native plane did not complete')
            got=bytes(ram[0xF0010+col*128:0xF0090+col*128]);want=[]
            ratio=trunc(((30-col)*65536)*65536,30*65536)
            rayx=cos-((sin*ratio)>>16);rayy=sin+((cos*ratio)>>16)
            for row in range(128):
                if sky:color=skydata[((angle>>22)&255)*128+row]
                elif row==64:color=0
                else:
                    distance=min(trunc(abs(height-z)*65536,abs(row-64)),0xFFFFFF)*128
                    wx=x*65536+((distance*rayx)>>16);wy=y*65536+((distance*rayy)>>16)
                    tx=(wx>>16)&63;ty=((-wy)>>16)&63;color=palette[flat[ty*64+tx]]
                want.append(color)
            assert got==bytes(want)
            assert c.p.sp_wrap==c.ddr_stats()['invalid']==c.ddr_stats()['hazards']==0
    finally:c.free()


def test_native_collision_reaches_line_2047_without_ram_overlap(motion_image):
    from test_doom_motion import Player
    lines=[(500,0,500,0,-32768,32767,0)]*2047+[(64,-128,64,128,0,0,1)]
    p=Player(motion_image,lines,block_ids=[2047])
    try:
        for _ in range(12):state=p.frame(forward=8)
        assert state['x']==48*65536 and state['blocked']&1
        assert p.c.xram[0xF1FF]&128
    finally:p.free()


def test_native_32nd_door_and_high_switch_mask_bit(motion_image):
    from test_doom_motion import Player
    for is_switch in (False,True):
        p=Player(motion_image,[(64,128,64,-128,0,0,2)],ceiling_b=0,door=True,door_count=32,manual_id=32,switch=is_switch,targets=1<<31)
        try:
            p.frame(buttons=1)
            doors=__import__('doom_motion').read_doors(p.c.xram)
            assert doors['count']==32 and doors['activations']==1 and doors['last_used']==32
            assert doors['states'][31]['phase']==1 and doors['states'][31]['height']==2
            assert all(d['phase']==0 for d in doors['states'][:31])
        finally:p.free()


# Import this fixture rather than cloning its native build implementation.
from test_doom_motion import motion_image


def test_original_state_graph_translation_is_complete_for_vendored_source():
    import re
    m=T.engine_metadata();source=(ROOT/'fw/doom/vendor/Doom8088/info.c').read_text()
    assert len(m['states'])==source.count('{SPR_')==314
    assert len(m['things'])==len(re.findall(r'// MT_\w+\n',source))==49
    assert m['states']['S_BOSS_DIE7']['action']=='A_BossDeath'
    assert m['states']['S_BRBALL1']['sprite']=='BAL7'
    assert m['states']['S_BRBALL1']['fullbright']


def test_translated_memory_checksums_are_checked_before_loading(tmp_path):
    image=b'native test image';raw=bytes(range(256))*16;boot=bytes(78);source=T.digest(b'WAD')
    (tmp_path/'assets.json').write_text(json.dumps(dict(wad_sha256=source)))
    info=dict(capacity=16384,firmware_sha256=T.digest(image),source_sha256=source,boot=boot.hex(),blocks=[dict(address=4096,bytes=4096,sha256=T.digest(raw))])
    def archive(payload):
        with zipfile.ZipFile(tmp_path/'ddr.zip','w') as z:z.writestr('memory.json',json.dumps(info));z.writestr('00001000.bin',payload)
    archive(raw);memory=bytearray(16384)
    got,assets=A.load_native(tmp_path,image,memory);assert got==boot and memory[4096:8192]==raw
    untouched=bytearray(b'\xa5'*16384)
    with pytest.raises(ValueError,match='firmware checksum'):A.load_native(tmp_path,b'wrong',untouched)
    assert untouched==b'\xa5'*16384
    archive(bytes(4096))
    with pytest.raises(ValueError,match='block checksum'):A.load_native(tmp_path,image,untouched)
    assert untouched==b'\xa5'*16384


def test_native_odd_health_overkill_does_not_break_accounting(combat_renderer,monkeypatch):
    from test_doom_combat import fixture_actors,POSE
    wad,out=combat_renderer;fixture_actors(monkeypatch,[(2240,-2392,150)])
    commands=[dict(buttons=2)]*40
    result,_=R.simulate(wad,out,initial_pose=POSE,commands=commands,frames=len(commands),save_frames=False,latency=64)
    combat=result['frames'][-1]['combat']
    assert combat['kills']==1 and combat['hits']==8
    assert result['frames'][-1]['actors']['things'][0]['health']==0

from test_doom_combat import combat_renderer


def test_asset_archive_has_reproducible_bytes(translated,tmp_path):
    path,out,_=translated;T.convert(path,tmp_path)
    assert T.digest((out/'doom-assets.dpak').read_bytes())==T.digest((tmp_path/'doom-assets.dpak').read_bytes())
