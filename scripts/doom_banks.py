"""Link a native projectile overlay against audited bank-zero exports."""
import json,re,hashlib
from pathlib import Path

def symbols(path):
    return {n:(int(a,16),space or '') for space,a,n in re.findall(r'^\s*(?:([CD]):)?\s*([0-9A-Fa-f]{8})\s+([_\w.$]+)\b',path.read_text(),re.M)}

def build(R,sdcc,linker,flags,out):
    base=R.ROOT/'fw/doom';src=(base/'projectiles.c').read_text()
    for n in ('Init','Spawn','Tick'):src=src.replace('Projectile'+n,'BankProjectile'+n)
    src=re.sub(r'__code __at\(0xFF94\).*?;','',src)
    (out/'projectile_engine.c').write_text(src)
    R.assemble_c(sdcc,[*flags,'-I'+str(base)],out/'projectile_engine.c',out/'projectile_engine.rel')
    rel=(out/'projectile_engine.rel').read_text().replace(' sdcccall(0)','');(out/'projectile_engine.rel').write_text(rel)
    # No bank-local DATA/bit variables may alias the common stack/register area.
    for area in ('DSEG','BSEG','ISEG','OSEG'):
        m=re.search(r'^A '+area+r' size ([0-9A-Fa-f]+)',rel,re.M)
        if m and int(m[1],16):raise ValueError('bank-local '+area+' requires explicit allocation')
    main=symbols(out/'doom_renderer.map')
    xbase=max(main.get('s_'+area,(0,''))[0]+main.get('l_'+area,(0,''))[0] for area in ('XSEG','XISEG','PSEG'))
    entry=''' .module projectile_entry
.globl _BankProjectileInit,_BankProjectileSpawn,_BankProjectileTick
.area ENTRY (ABS,CODE)
.org 0x5000
ljmp _BankProjectileInit
ljmp _BankProjectileSpawn
ljmp _BankProjectileTick
'''
    (out/'projectile_entry.asm').write_text(entry)
    R.run([sdcc.parent/'sdas8051','-losg',out/'projectile_entry.rel',out/'projectile_entry.asm'])
    lines=['-muwx','-i '+str(out/'projectile_engine.ihx'),'-b CSEG=0x5010','-b CONST=0x7000','-b XSEG=0x%X'%xbase]
    imports={}
    for n in re.findall(r'^S (\S+) Ref',rel,re.M):
        if n=='.__.ABS.':continue
        if n not in main:raise ValueError('bank-zero export missing: '+n)
        address,space=main[n]
        if space=='C' and 0x5000<=address<0x7100:raise ValueError('overlay masks its own dependency: '+n)
        imports[n]=address;lines.append('-g '+n+'=0x%X'%address)
    lines.extend([str(out/'projectile_entry.rel'),str(out/'projectile_engine.rel'),''])
    (out/'projectile_engine.lk').write_text('\n'.join(lines))
    R.run([linker.parent/'sdld','-nf',out/'projectile_engine.lk'])
    engine=symbols(out/'projectile_engine.map')
    for area in ('GSINIT','XINIT','XISEG'):
        if engine.get('l_'+area,(0,''))[0]:raise ValueError('unsupported bank-local initializer area '+area)
    end=engine['s_CSEG'][0]+engine['l_CSEG'][0]
    if end>0x7000 or engine.get('l_CONST',(0,''))[0]:raise ValueError('projectile overlay exceeded audited range')
    xend=engine['s_XSEG'][0]+engine['l_XSEG'][0]
    if xend>0xE000:raise ValueError('projectile engine exceeds dynamic MCU XRAM')
    import doom_sim as S
    b0=S.load_ihx(out/'doom_renderer.ihx');overlay=S.load_ihx(out/'projectile_engine.ihx')
    b1=bytearray(b0);b1[0x5000:end]=overlay[0x5000:end]
    assert b0[:0x5000]==b1[:0x5000]
    (out/'doom_renderer.bin').write_bytes(b0+b1)
    info=dict(bank0_sha256=hashlib.sha256(b0).hexdigest(),image_sha256=hashlib.sha256(b0+b1).hexdigest(),banks=2,overlay_start=0x5000,overlay_end=end,common_end=0x5000,imports=imports,
              engine_xram_start=xbase,engine_xram_end=xend,engine_xram_bytes=xend-xbase,
              note='Two native code banks; common bytes and callable dependencies are duplicated. Bank selection uses the existing simulator MOVX FFFF model, not verified monitor register wiring.')
    (out/'banking.json').write_text(json.dumps(info,indent=2))
