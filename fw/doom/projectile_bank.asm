; Native fireball/pickup trampolines. Identical wrapper bytes in both banks.
; ABI 1: Spawn's uint16 owner arrives in DPTR. No interrupts in this image.
.module projectile_bank
.globl _ProjectileInit,_ProjectileSpawn,_ProjectileTick
.globl _PickupInit,_PickupTick
.globl _R_DrawCombatHUD,_R_DrawPlaneBank
.area CSEG (CODE)
_R_DrawPlaneBank:
    mov dptr,#0xffff
    mov a,#2
    movx @dptr,a
    lcall 0x5003
    ljmp leave
_R_DrawCombatHUD:
    mov dptr,#0xffff
    mov a,#2
    movx @dptr,a
    lcall 0x5000
    ljmp leave
_ProjectileInit:
    mov r7,#0
    sjmp enter
_ProjectileSpawn:
    mov r7,#1
    sjmp enter
_ProjectileTick:
    mov r7,#2
    sjmp enter
_PickupInit:
    mov r7,#3
    sjmp enter
_PickupTick:
    mov r7,#4
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
    cjne a,#1,checktick
    lcall 0x5003
    sjmp leave
init:
    lcall 0x5000
    sjmp leave
checktick:
    cjne a,#2,checkpickup
    lcall 0x5006
    sjmp leave
checkpickup:
    cjne a,#3,pickuptick
    lcall 0x5009
    sjmp leave
pickuptick:
    lcall 0x500c
leave:
    mov dptr,#0xffff
    clr a
    movx @dptr,a
    ret
.area CABS (ABS,CODE)
.org 0xff94
.dw 16,8
.org 0xff98
.dw 128,8
