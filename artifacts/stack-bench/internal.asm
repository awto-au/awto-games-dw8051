.module stackbench
.globl _foo
.area REG_BANK_0 (REL,OVR,DATA)
rbank0: .ds 8
.area DSEG (DATA)
bp: .ds 1
bpx: .ds 1
_spx: .ds 1
.area CSEG (CODE)
_foo:
	ar7 = rbank0 + 0x07
	ar6 = rbank0 + 0x06
	ar5 = rbank0 + 0x05
	ar4 = rbank0 + 0x04
	ar3 = rbank0 + 0x03
	ar2 = rbank0 + 0x02
	ar1 = rbank0 + 0x01
	ar0 = rbank0 + 0x00
	push	bp
	mov	bp,sp
	mov	r4,dpl
	mov	r5,dph
	mov	r6,b
	mov	r7,a
	mov	a,bp
	add	a,#0xfa
	mov	r0,a
	mov	a,@r0
	add	a, r4
	mov	r4,a
	inc	r0
	mov	a,@r0
	addc	a, r5
	mov	r5,a
	inc	r0
	mov	a,@r0
	addc	a, r6
	mov	r6,a
	inc	r0
	mov	a,@r0
	addc	a, r7
	mov	dpl,r4
	mov	dph,r5
	mov	b,r6
	pop	bp
	ret
