; SDCC little-endian --model-large --stack-auto --sdcccall 0.
; a = DPL,DPH,B,A; b is four caller-pushed bytes below the return address.
.module doom_fixed_stack_abi
.globl _FixedMul, _FixedDiv, _DoomFixedMul, _DoomFixedDiv
.globl _DdrWriteStack, _DdrWrite
acc = 0xe0
b = 0xf0
.area CSEG (CODE)
_DdrWriteStack:
push acc
mov a,sp
add a,#0xfd
mov r0,a
mov a,@r0
mov r7,a
pop acc
ljmp _DdrWrite
_FixedMul:
mov r7,dpl
mov r6,dph
mov r5,b
mov r4,a
lcall load_b
lcall _DoomFixedMul
sjmp result
_FixedDiv:
mov r7,dpl
mov r6,dph
mov r5,b
mov r4,a
lcall load_b
lcall _DoomFixedDiv
result:
mov dpl,r7
mov dph,r6
mov b,r5
mov a,r4
ret
load_b:
; Our own LCALL added two more return-address bytes: entry SP - 7.
mov a,sp
add a,#0xf9
mov r1,a
mov a,@r1
mov r3,a
inc r1
mov a,@r1
mov r2,a
inc r1
mov a,@r1
push acc
inc r1
mov a,@r1
mov r0,a
pop acc
mov r1,a
ret
