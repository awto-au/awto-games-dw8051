; SDCC little-endian, --model-large, --sdcccall 0 wrappers.
; First long: DPL,DPH,B,A. Second long: XDATA parameter slot.
; The private maths use R4..R7 / R0..R3, MSB first.
.module doom_fixed_abi
.globl _FixedMul, _FixedDiv, _FixedMul_PARM_2, _FixedDiv_PARM_2
.globl _DoomFixedMul, _DoomFixedDiv
b = 0xf0
.area XSEG (XDATA)
_FixedMul_PARM_2: .ds 4
_FixedDiv_PARM_2: .ds 4
.area CSEG (CODE)
_FixedMul:
mov r7,dpl
mov r6,dph
mov r5,b
mov r4,a
mov dptr,#_FixedMul_PARM_2
lcall load_b
lcall _DoomFixedMul
sjmp result
_FixedDiv:
mov r7,dpl
mov r6,dph
mov r5,b
mov r4,a
mov dptr,#_FixedDiv_PARM_2
lcall load_b
lcall _DoomFixedDiv
result:
mov dpl,r7
mov dph,r6
mov b,r5
mov a,r4
ret
load_b:
movx a,@dptr
mov r3,a
inc dptr
movx a,@dptr
mov r2,a
inc dptr
movx a,@dptr
mov r1,a
inc dptr
movx a,@dptr
mov r0,a
ret
