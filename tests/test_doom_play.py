"""End-to-end HTTP input -> native door ticks -> framebuffer/MJPEG output."""
import json,os,struct,threading,time,urllib.request,urllib.error
from pathlib import Path
import pytest
from test_doom_platform import toolchain
import doom_renderer as R,doom_play as P

@pytest.fixture(scope='module')
def renderer(tmp_path_factory):
    wad=os.environ.get('AWTO_DOOM_WAD')
    if not wad:pytest.skip('set AWTO_DOOM_WAD')
    out=tmp_path_factory.mktemp('door-renderer');sdcc,linker,lib=toolchain(True)
    R.build(sdcc,linker,lib,out,width=60,height=128)
    return Path(wad),out


def test_native_door_sequence_and_extended_frame_count(renderer):
    wad,out=renderer
    root=Path(__file__).resolve().parents[1]
    commands=json.loads((root/'examples/doom-door.json').read_text())
    pose=json.loads((root/'examples/doom-door-pose.json').read_text())
    result,_=R.simulate(wad,out,frames=len(commands),commands=commands,initial_pose=pose,latency=64)
    assert len(result['frames'])==310
    assert result['frames'][-1]['motion']['ticks']==434
    assert all(f['world_verified'] and f['motion_verified'] for f in result['frames'])
    assert result['frames'][5]['motion']['x']<1536*65536
    assert result['frames'][40]['motion']['x']>1536*65536
    # The compiler/private-DDR pointer-tag regression made these views black.
    assert all(result['frames'][i]['palette_indices']>3 for i in (40,100,150))
    final=result['frames'][-1]['doors']
    assert final['reopens']==1 and final['activations']==1
    assert final['states'][0]['height']==0 and final['states'][0]['phase']==0
    assert all(f['doors']['fault']==0 for f in result['frames'])
    assert result['stack_wraps']==0
    # Every exact original high word is retained in the native DDR table.
    tables=json.loads((out/'tables.json').read_text())
    table=next(t for t in tables if t['name']=='tantoangle16')
    full=(out/'tantoangleTable.bin').read_bytes()
    assert bytes.fromhex(table['hex'])==b''.join(full[i+2:i+4] for i in range(0,len(full),4))



def test_http_live_input_jpeg_and_stream(renderer):
    wad,out=renderer
    session=P.PlaySession(preview_hz=50);server=P.make_server(session,0)
    threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
    def post(path,body=None):
        request=urllib.request.Request(url+path,data=json.dumps(body or {}).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request,timeout=5) as response:return json.load(response)
    errors=[];results=[]
    pose=dict(x=1488*65536,y=-2496*65536,angle=0,viewz=41*65536)
    def run():
        try:results.append(R.simulate(wad,out,frames=1000,initial_pose=pose,latency=64,input_provider=session.command,on_frame=session.frame,save_frames=False)[0])
        except BaseException as error:errors.append(error)
    try:
        with urllib.request.urlopen(url,timeout=5) as response:assert b'Native combat prototype' in response.read()
        post('/input',dict(buttons=1));post('/input',dict(buttons=0))  # quick tap is latched
        worker=threading.Thread(target=run,daemon=True);worker.start()
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            with session.condition:state=session.state.copy()
            if state.get('frame',-1)>=2 or errors:break
            time.sleep(0.01)
        assert not errors,errors
        assert state['doors']['activations']==1
        with urllib.request.urlopen(url+'/frame.jpg',timeout=5) as response:assert response.read().startswith(b'\xff\xd8')
        with urllib.request.urlopen(url+'/stream',timeout=5) as response:
            assert 'multipart/x-mixed-replace' in response.headers['Content-Type']
            assert b'Content-Type: image/jpeg' in response.read(100)
        with pytest.raises(urllib.error.HTTPError) as error:post('/input',dict(buttons=999))
        assert error.value.code==400
        assert post('/stop')['stopped']
        worker.join(10);assert not worker.is_alive() and not errors,errors
        assert results[0]['stopped'] and len(results[0]['frames'])<1000
        assert results[0]['palette_verified']
    finally:
        session.stop.set()
        with session.condition:session.condition.notify_all()
        server.shutdown();server.server_close()
