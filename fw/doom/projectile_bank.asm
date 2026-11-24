; Native bank trampolines. The same wrapper bytes exist in both code banks.
; ABI 1: Spawn's uint16 owner arrives in DPTR. No interrupts in this image.
.module projectile_bank
.globl _ProjectileInit,_ProjectileSpawn,_ProjectileTick
.area CSEG (CODE)
_ProjectileInit:
    mov r7,#0
    sjmp enter
_ProjectileSpawn:
    mov r7,#1
    sjmp enter
_ProjectileTick:
    mov r7,#2
enter:
    push dpl
    push dph
    mov dptr,#0xffff
    mov a,#1
    movx @dptr,a
    pop dph
    pop dpl
    mov a,r7
    jz init
    cjne a,#1,tick
    lcall 0x5003
    sjmp leave
init:
    lcall 0x5000
    sjmp leave
tick:
    lcall 0x5006
leave:
    mov dptr,#0xffff
    clr a
    movx @dptr,a
    ret
.area CABS (ABS,CODE)
.org 0xff94
.dw 16,8
