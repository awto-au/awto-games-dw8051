#!/usr/bin/env python3
"""Launch a prepared native map after extracting this download."""
import argparse,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--map',default='E1M1',choices=[f'E1M{i}' for i in range(1,10)])
p.add_argument('--port',type=int,default=8099)
p.add_argument('--frames',type=int,default=65535)
a=p.parse_args();root=Path(__file__).resolve().parent;source=root;scene=root/'translated/native'/a.map
if not (scene/'ddr.zip').exists():p.error('translated/native/<map> is missing')
env=os.environ.copy();env['AWTO_DDC_REPO']=str(source)
raise SystemExit(subprocess.call([sys.executable,str(source/'scripts/doom_play.py'),'--out',str(scene),'--packed',str(scene),'--port',str(a.port),'--frames',str(a.frames)],cwd=source,env=env))
