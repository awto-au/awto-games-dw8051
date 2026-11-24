#!/usr/bin/env python3
"""Check all archive payload hashes using only the Python standard library."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;manifest=json.loads((root/'download-manifest.json').read_text());bad=[]
for entry in manifest['files']:
 path=root/entry['path']
 if not path.is_file() or path.stat().st_size!=entry['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:bad.append(entry['path'])
if bad:raise SystemExit('Verification failed: '+', '.join(bad))
print(f"Verified {len(manifest['files'])} files, including the original Doom shareware WAD.")
