#!/usr/bin/env python3
"""Keyboard-controlled native Doom walkthrough prototype + MJPEG/VLC stream.

Input is the only host-to-CPU change after boot. Physics, doors and pixels run
on the DW8051 core. The host preview's 25 Hz cap is not hardware performance.
"""
import argparse
import io
import json
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import doom_renderer as R
import doom_motion as M

PAGE='''<!doctype html><meta charset="utf-8"><title>Native scaler walkthrough</title>
<style>body{background:#17191c;color:#e8e8e8;font:16px system-ui;margin:24px auto;max-width:980px}img{width:100%;image-rendering:pixelated;background:black;aspect-ratio:15/8}button{font:inherit;padding:8px 20px}#status{font-variant-numeric:tabular-nums}</style>
<h1>Native scaler walkthrough</h1><p>W/S: forward/back · A/D: strafe · arrows: turn · Space/E: use door · F/Ctrl: fire · Shift: faster</p>
<p>Native combat prototype. Pistol, health, ammo and ground monsters work. Imps throw fireballs; soldiers fire from range. Sound is not implemented. At zero health, stop and restart the simulator.</p>
<img src="/stream" alt="Native framebuffer"><p id="status">Starting simulator…</p><button id="stop">Stop</button>
<script>const held=new Set();let stopped=false;
const controls=new Set(['KeyW','KeyS','KeyA','KeyD','ArrowLeft','ArrowRight','Space','KeyE','ShiftLeft','ShiftRight','KeyF','ControlLeft','ControlRight']);
function command(){let speed=held.has('ShiftLeft')||held.has('ShiftRight')?8:4;return {enabled:1,forward:speed*((held.has('KeyW')?1:0)-(held.has('KeyS')?1:0)),strafe:speed*((held.has('KeyA')?1:0)-(held.has('KeyD')?1:0)),turn:768*((held.has('ArrowLeft')?1:0)-(held.has('ArrowRight')?1:0)),buttons:((held.has('Space')||held.has('KeyE'))?1:0)|((held.has('KeyF')||held.has('ControlLeft')||held.has('ControlRight'))?2:0)};}
async function send(){if(!stopped)try{await fetch('/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(command())});}catch(e){}}
onkeydown=e=>{if(controls.has(e.code)){e.preventDefault();held.add(e.code);send();}};
onkeyup=e=>{if(controls.has(e.code)){e.preventDefault();held.delete(e.code);send();}};
onblur=()=>{held.clear();send();};document.onvisibilitychange=()=>{if(document.hidden){held.clear();send();}};
setInterval(send,100);setInterval(async()=>{if(stopped)return;try{let s=await(await fetch('/state')).json();if(s.frame!==undefined)document.getElementById('status').textContent=`Frame ${s.frame} · CPU-model frame ${s.model_ms.toFixed(1)} ms · use activations ${s.doors.activations}${s.combat ? ` · Health ${s.combat.health} · Ammo ${s.combat.ammo} · Kills ${s.combat.kills}${s.combat.dead ? ' · DEAD' : ''}` : ''}`;}catch(e){}},250);
document.getElementById('stop').onclick=async()=>{held.clear();await send();stopped=true;try{await fetch('/stop',{method:'POST'});}catch(e){}document.getElementById('status').textContent='Stopped';};</script>'''

class PlaySession:
    def __init__(self,preview_hz=25):
        self.condition=threading.Condition();self.latest=dict(enabled=1)
        self.updated=time.monotonic();self.stop=threading.Event();self.jpeg=b'';self.state={};self.sequence=0;self.pending_buttons=0
        self.interval=1/preview_hz if preview_hz else 0;self.next_frame=time.monotonic()
    def command(self,index):
        with self.condition:
            command=self.latest.copy() if time.monotonic()-self.updated<0.5 else dict(enabled=1)
            if self.pending_buttons:command['buttons']=command.get('buttons',0)|self.pending_buttons;self.pending_buttons=0
            return command
    def set_command(self,value):
        if not isinstance(value,dict):raise ValueError('expected command object')
        try:M.pack_command(value)
        except (TypeError,ValueError,OverflowError,struct.error) as error:raise ValueError('invalid command') from error
        with self.condition:
            self.pending_buttons|=value.get('buttons',0)&~self.latest.get('buttons',0)&3
            self.latest=value.copy();self.updated=time.monotonic()
    def frame(self,image,record,index):
        from PIL import Image
        preview=image.resize((480,256),Image.Resampling.NEAREST)
        buf=io.BytesIO();preview.save(buf,'JPEG',quality=90)
        with self.condition:
            self.jpeg=buf.getvalue();self.state=dict(record,frame=index);self.sequence+=1;self.condition.notify_all()
        self.next_frame=max(self.next_frame+self.interval,time.monotonic())
        self.stop.wait(max(0,self.next_frame-time.monotonic()))
        return not self.stop.is_set()

def make_server(session,port=8099):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,body,content_type='application/json'):
            if not isinstance(body,bytes):body=json.dumps(body).encode()
            self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path=='/':return self.reply(200,PAGE.encode(),'text/html; charset=utf-8')
            if self.path=='/state':
                with session.condition:state=session.state.copy()
                return self.reply(200,state)
            if self.path=='/frame.jpg':
                with session.condition:jpg=session.jpeg
                return self.reply(200,jpg,'image/jpeg')
            if self.path!='/stream':return self.reply(404,{'error':'not found'})
            self.send_response(200);self.send_header('Content-Type','multipart/x-mixed-replace; boundary=frame');self.end_headers();last=-1
            try:
                while not session.stop.is_set():
                    with session.condition:
                        session.condition.wait_for(lambda:session.sequence!=last or session.stop.is_set(),timeout=1)
                        jpg,last=session.jpeg,session.sequence
                    if jpg:self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: '+str(len(jpg)).encode()+b'\r\n\r\n'+jpg+b'\r\n');self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError):pass
        def do_POST(self):
            if self.path=='/stop':session.stop.set();return self.reply(200,{'stopped':True})
            if self.path!='/input':return self.reply(404,{'error':'not found'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2048:raise ValueError('invalid length')
                session.set_command(json.loads(self.rfile.read(length)))
            except (ValueError,TypeError,OverflowError,UnicodeError):return self.reply(400,{'error':'invalid input'})
            return self.reply(200,{'accepted':True})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
    return server

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True,help='existing doom_renderer build directory')
    p.add_argument('--wad',type=Path,required=True);p.add_argument('--pose',type=Path);p.add_argument('--port',type=int,default=8099)
    p.add_argument('--frames',type=int,default=65535);p.add_argument('--latency',type=int,default=64)
    a=p.parse_args();session=PlaySession();server=make_server(session,a.port)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    print(f'Keyboard preview http://127.0.0.1:{server.server_port}/',flush=True)
    print(f'VLC stream http://127.0.0.1:{server.server_port}/stream',flush=True)
    try:
        R.simulate(a.wad,a.out,frames=a.frames,initial_pose=json.loads(a.pose.read_text()) if a.pose else None,
                   input_provider=session.command,on_frame=session.frame,save_frames=False,latency=a.latency)
    except KeyboardInterrupt:pass
    finally:
        session.stop.set()
        with session.condition:session.condition.notify_all()
        server.shutdown();server.server_close()

if __name__=='__main__':main()
