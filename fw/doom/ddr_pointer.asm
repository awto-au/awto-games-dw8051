; Generic pointer bridge, SDCC large model, register bank zero, no interrupts.
; Tags 01..3f access DDR through the native cache. Normal SDCC tags preserved.
; Preserve all registers, DPTR, B and PSW, except the documented ACC result.
.module doom_ddr_pointer
.include "doom_cache_config.inc"
.globl __gptrget, __gptrput
.globl _DdrRead, _DdrWrite
acc = 0xe0
b = 0xf0
psw = 0xd0
dpl1 = 0x84
dph1 = 0x85
dps = 0x86
.area CSEG (CODE)
__gptrget:
push psw
mov a,b
jz get_xram
jb acc.7,get_code
cjne a,#0x40,get_pdata_test
push 0x00
mov r0,dpl
mov a,@r0
pop 0x00
pop psw
ret
get_pdata_test:
cjne a,#0x60,get_ddr
push 0x00
mov r0,dpl
movx a,@r0
pop 0x00
pop psw
ret
get_code:
clr a
movc a,@a+dptr
pop psw
ret
get_xram:
movx a,@dptr
pop psw
ret
get_ddr:
jnb acc.6,get_valid_ddr
ljmp bad_tag
get_valid_ddr:
; DPTR0 and B keep the generic address. DPTR1 probes the SRAM cache.
push 0x00
push 0x01
push dps
push dpl1
push dph1
lcall lookup
jnc get_fast_miss
mov dpl1,dpl
mov a,dph
anl a,#0x07
add a,#(DOOM_CACHE_DATA_BASE >> 8)
mov dph1,a
movx a,@dptr
pop dph1
pop dpl1
pop dps
pop 0x01
pop 0x00
pop psw
ret
get_fast_miss:
pop dph1
pop dpl1
pop dps
pop 0x01
pop 0x00
lcall save
clr a
lcall _DdrRead
mov a,dpl
ljmp restore
__gptrput:
push psw
push acc
mov a,b
jz put_xram
jnb acc.7,put_not_code
ljmp bad_tag
put_not_code:
cjne a,#0x40,put_pdata_test
pop acc
push 0x00
mov r0,dpl
mov @r0,a
pop 0x00
pop psw
ret
put_pdata_test:
cjne a,#0x60,put_ddr
pop acc
push 0x00
mov r0,dpl
movx @r0,a
pop 0x00
pop psw
ret
put_xram:
pop acc
movx @dptr,a
pop psw
ret
put_ddr:
jnb acc.6,put_valid_ddr
ljmp bad_tag
put_valid_ddr:
pop acc
push acc
push 0x00
push 0x01
push dps
push dpl1
push dph1
lcall lookup
jnc put_fast_miss
; A matching generic bank is below 4 MiB, so bank bit 8 is zero.
mov a,#((DOOM_CACHE_VALID | DOOM_CACHE_DIRTY) >> 8)
movx @dptr,a
mov dpl1,dpl
mov a,dph
anl a,#0x07
add a,#(DOOM_CACHE_DATA_BASE >> 8)
mov dph1,a
mov a,sp
add a,#0xfb
mov r1,a
mov a,@r1
movx @dptr,a
pop dph1
pop dpl1
pop dps
pop 0x01
pop 0x00
pop acc
pop psw
ret
put_fast_miss:
pop dph1
pop dpl1
pop dps
pop 0x01
pop 0x00
pop acc
; Inline saves: a subroutine cannot leave its return address under the frame.
push acc
push 0x00
push 0x01
push 0x02
push 0x03
push 0x04
push 0x05
push 0x06
push 0x07
push dpl
push dph
push b
push psw
mov r7,a
clr a
lcall _DdrWrite
lcall restore_put
pop acc
pop psw
ret
bad_tag:
sjmp bad_tag

; save/restore must move their own return address around the saved frame.
save:
pop acc
mov save_ret_lo,a
pop acc
mov save_ret_hi,a
push 0x00
push 0x01
push 0x02
push 0x03
push 0x04
push 0x05
push 0x06
push 0x07
push dpl
push dph
push b
push psw
push save_ret_hi
push save_ret_lo
ret
restore_put:
pop acc
mov save_ret_lo,a
pop acc
mov save_ret_hi,a
pop psw
pop b
pop dph
pop dpl
pop 0x07
pop 0x06
pop 0x05
pop 0x04
pop 0x03
pop 0x02
pop 0x01
pop 0x00
push save_ret_hi
push save_ret_lo
ret
restore:
pop psw
pop b
pop dph
pop dpl
pop 0x07
pop 0x06
pop 0x05
pop 0x04
pop 0x03
pop 0x02
pop 0x01
pop 0x00
pop psw
ret
; Hit: C=1, DPS.0=1, DPTR1 at the high bank/flags byte.
; Miss: C=0. R0/R1 and DPTR1 scratch only; DPTR0/B never change.
; SoA table layout and 128-line geometry are fixed by cache_config.h.
lookup:
mov a,dpl
swap a
anl a,#0x0f
mov r0,a
mov a,dph
anl a,#0x07
swap a
orl a,r0
rl a
mov r0,a
mov dpl1,a
mov dph1,#(DOOM_CACHE_OFFSETS_BASE >> 8)
orl dps,#1
movx a,@dptr
mov r1,a
mov a,dpl
anl a,#0xf0
xrl a,r1
jnz lookup_miss
inc dptr
movx a,@dptr
xrl a,dph
jnz lookup_miss
mov dpl1,r0
mov dph1,#(DOOM_CACHE_BANKS_BASE >> 8)
movx a,@dptr
xrl a,b
jnz lookup_miss
inc dptr
movx a,@dptr
anl a,#0x7f
cjne a,#(DOOM_CACHE_VALID >> 8),lookup_miss
setb c
ret
lookup_miss:
clr c
ret
.area DSEG (DATA)
save_ret_lo: .ds 1
save_ret_hi: .ds 1
