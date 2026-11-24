"""Native loop source and fixed SRAM layout contracts."""
import runpy
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

@pytest.mark.parametrize('name,assembly',[('doom_video_gen','video'),('doom_cache_gen','cache_native')])
def test_generated_native_loops_match_checked_in_assembly(name,assembly):
    result=runpy.run_path(str(ROOT/'scripts'/f'{name}.py'))
    assert '\n'.join(result['out'])+'\n' == (ROOT/'fw/doom'/f'{assembly}.asm').read_text()

@pytest.mark.parametrize('width,height',[(30,64),(40,96),(60,128)])
def test_tile_padding_and_sram_pages(tmp_path,width,height):
    import doom_renderer as R
    cfg=R.cache_config(tmp_path,{'DOOM_VIEW_WIDTH':width,'DOOM_VIEW_HEIGHT':height})
    pitch=cfg['DOOM_RASTER_PITCH']
    assert pitch >= ((width+15)//16)*48
    assert pitch%16 == 0
    assert R.cache_config(tmp_path)==cfg
    assert sum(cfg[f'DOOM_RASTER_BASE_BYTE{b}']<<(b*8) for b in range(4)) == cfg['DOOM_RASTER_BASE']
    ranges=[(cfg['DOOM_CACHE_DATA_BASE'],128*16),(cfg['DOOM_CACHE_OFFSETS_BASE'],128*2),
            (cfg['DOOM_CACHE_BANKS_BASE'],128*2),(cfg['DOOM_CACHE_PALETTE_BASE'],768),
            (cfg['DOOM_CACHE_BURST_BASE'],48),(cfg['DOOM_TEXTURE_COLUMN_BASE'],128),
            (cfg['DOOM_COLORMAP_BASE'],256),(cfg['DOOM_TILE_BASE'],256),
            (cfg['DOOM_FRAME_BITMAP_BASE'],cfg['DOOM_FRAME_BITMAP_BYTES'])]
    for start,size in ranges: assert 0xE000<=start<start+size<=0xF600
    for (start,size),(next_start,_) in zip(ranges,ranges[1:]): assert start+size<=next_start
