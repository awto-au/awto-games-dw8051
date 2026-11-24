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
	mov	r0,_spx
	inc	_spx
	xch	a,bpx
	movx	@r0,a
	inc	r0
	mov	a,r0
	xch	a,bpx
	push	bp
	mov	bp,sp
	inc	sp
	inc	sp
	inc	sp
	inc	sp
	mov	r0,bp
	inc	r0
	mov	@r0, dpl
	inc	r0
	mov	@r0, dph
	inc	r0
	mov	@r0, b
	inc	r0
	mov	@r0,a
	mov	a,bpx
	add	a,#0xfb
	mov	r0,a
	movx	a,@r0
	mov	r2,a
	inc	r0
	movx	a,@r0
	mov	r3,a
	inc	r0
	movx	a,@r0
	mov	r6,a
	inc	r0
	movx	a,@r0
	mov	r7,a
	mov	r0,bp
	inc	r0
	mov	a,r2
	add	a, @r0
	mov	r2,a
	mov	a,r3
	inc	r0
	addc	a, @r0
	mov	r3,a
	mov	a,r6
	inc	r0
	addc	a, @r0
	mov	r6,a
	mov	a,r7
	inc	r0
	addc	a, @r0
	mov	dpl,r2
	mov	dph,r3
	mov	b,r6
	mov	sp,bp
	pop	bp
	xch	a,bpx
	mov	r0,a
	dec	r0
	movx	a,@r0
	xch	a,bpx
	mov	_spx,r0
	ret
