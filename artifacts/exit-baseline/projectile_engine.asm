;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.6.4 #0 (Linux)
;--------------------------------------------------------
	.module projectile_engine
	
	.optsdcc -mmcs51 --model-large
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _BankPickupTick
	.globl _BankPickupInit
	.globl _BankProjectileTick
	.globl _BankProjectileSpawn
	.globl _BankProjectileInit
	.globl _PlayerDamage
	.globl _MotionSectorAt
	.globl _MotionVisible
	.globl _DdrPointer
	.globl _FixedDiv
	.globl _projectile_info
;--------------------------------------------------------
; special function registers
;--------------------------------------------------------
	.area RSEG    (ABS,DATA)
	.org 0x0000
;--------------------------------------------------------
; special function bits
;--------------------------------------------------------
	.area RSEG    (ABS,DATA)
	.org 0x0000
;--------------------------------------------------------
; overlayable register banks
;--------------------------------------------------------
	.area REG_BANK_0	(REL,OVR,DATA)
rbank0:	.ds 8
;--------------------------------------------------------
; internal ram data
;--------------------------------------------------------
	.area DSEG    (DATA)
;--------------------------------------------------------
; overlayable items in internal ram
;--------------------------------------------------------
;--------------------------------------------------------
; indirectly addressable internal ram data
;--------------------------------------------------------
	.area ISEG    (DATA)
;--------------------------------------------------------
; absolute internal ram data
;--------------------------------------------------------
	.area IABS    (ABS,DATA)
	.area IABS    (ABS,DATA)
;--------------------------------------------------------
; bit data
;--------------------------------------------------------
	.area BSEG    (BIT)
;--------------------------------------------------------
; paged external ram data
;--------------------------------------------------------
	.area PSEG    (PAG,XDATA)
;--------------------------------------------------------
; uninitialized external ram data
;--------------------------------------------------------
	.area XSEG    (XDATA)
_projectile_info	=	0xf720
_projectile_states:
	.ds 3
_projectile_sprites:
	.ds 3
_BankProjectileInit_i_10000_43:
	.ds 1
_BankProjectileInit_header_10000_43:
	.ds 3
_BankProjectileSpawn_i_10000_47:
	.ds 1
_BankProjectileSpawn_dx_10000_47:
	.ds 2
_BankProjectileSpawn_dy_10000_47:
	.ds 2
_BankProjectileSpawn_den_10000_47:
	.ds 2
_BankProjectileSpawn_p_10000_47:
	.ds 3
_BankProjectileSpawn_v_10000_47:
	.ds 3
_BankProjectileSpawn_header_10000_47:
	.ds 3
_BankProjectileTick_i_10000_55:
	.ds 1
_BankProjectileTick_step_10000_55:
	.ds 1
_BankProjectileTick_x_10000_55:
	.ds 2
_BankProjectileTick_y_10000_55:
	.ds 2
_BankProjectileTick_nx_10000_55:
	.ds 2
_BankProjectileTick_ny_10000_55:
	.ds 2
_BankProjectileTick_dx_10000_55:
	.ds 2
_BankProjectileTick_dy_10000_55:
	.ds 2
_BankProjectileTick_p_10000_55:
	.ds 3
_BankProjectileTick_v_10000_55:
	.ds 3
_pickup_things:
	.ds 3
_pickup_count:
	.ds 2
_BankPickupInit_i_10000_73:
	.ds 2
_BankPickupInit_header_10000_73:
	.ds 3
_BankPickupInit_ceiling_10000_73:
	.ds 2
_BankPickupTick_i_10000_82:
	.ds 2
_BankPickupTick_amount_10000_82:
	.ds 2
_BankPickupTick_value_10000_82:
	.ds 2
_BankPickupTick_cap_10000_82:
	.ds 2
_BankPickupTick_x_10000_82:
	.ds 2
_BankPickupTick_y_10000_82:
	.ds 2
_BankPickupTick_dx_10000_82:
	.ds 2
_BankPickupTick_dy_10000_82:
	.ds 2
_BankPickupTick_dz_10000_82:
	.ds 2
_BankPickupTick_p_10000_82:
	.ds 3
;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area XABS    (ABS,XDATA)
;--------------------------------------------------------
; initialized external ram data
;--------------------------------------------------------
	.area XISEG   (XDATA)
	.area HOME    (CODE)
	.area GSINIT0 (CODE)
	.area GSINIT1 (CODE)
	.area GSINIT2 (CODE)
	.area GSINIT3 (CODE)
	.area GSINIT4 (CODE)
	.area GSINIT5 (CODE)
	.area GSINIT  (CODE)
	.area GSFINAL (CODE)
	.area CSEG    (CODE)
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area HOME    (CODE)
	.area GSINIT  (CODE)
	.area GSFINAL (CODE)
	.area GSINIT  (CODE)
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area HOME    (CODE)
	.area HOME    (CODE)
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area CSEG    (CODE)
;------------------------------------------------------------
;Allocation info for local variables in function 'BankProjectileInit'
;------------------------------------------------------------
;i             Allocated with name '_BankProjectileInit_i_10000_43'
;header        Allocated with name '_BankProjectileInit_header_10000_43'
;------------------------------------------------------------
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:13: void BankProjectileInit(void) __sdcccall(1)
;	-----------------------------------------
;	 function BankProjectileInit
;	-----------------------------------------
_BankProjectileInit:
	ar7 = rbank0 + 0x07
	ar6 = rbank0 + 0x06
	ar5 = rbank0 + 0x05
	ar4 = rbank0 + 0x04
	ar3 = rbank0 + 0x03
	ar2 = rbank0 + 0x02
	ar1 = rbank0 + 0x01
	ar0 = rbank0 + 0x00
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:17: header=DdrPointer(0xD0010UL);header[1]=actor_count+8;
	mov	dptr,#0x0010
	mov	b, #0x0d
	clr	a
	lcall	_DdrPointer
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
	mov	dptr,#_BankProjectileInit_header_10000_43
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	a,#0x02
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dptr,#_actor_count
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,#0x08
	add	a, r3
	mov	r3,a
	clr	a
	addc	a, r4
	mov	r4,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,r3
	lcall	__gptrput
	inc	dptr
	mov	a,r4
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:18: projectile_states=DdrPointer(0xD6010UL);
	mov	dptr,#0x6010
	mov	b, #0x0d
	clr	a
	lcall	_DdrPointer
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
	mov	dptr,#_projectile_states
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:19: projectile_sprites=actor_things+actor_count;
	mov	dptr,#_actor_things
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	push	ar7
	push	ar6
	push	ar5
	mov	dptr,#_actor_count
	movx	a,@dptr
	push	acc
	inc	dptr
	movx	a,@dptr
	push	acc
	mov	dptr,#0x0014
	lcall	__mulint
	mov	r3, dpl
	mov	r4, dph
	dec	sp
	dec	sp
	pop	ar5
	pop	ar6
	pop	ar7
	mov	dptr,#_projectile_sprites
	mov	a,r3
	add	a, r5
	movx	@dptr,a
	mov	a,r4
	addc	a, r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:20: for(i=0;i<8;++i){projectile_info[i]=0;projectile_sprites[i].health=0;}
	mov	dptr,#_BankProjectileInit_i_10000_43
	clr	a
	movx	@dptr,a
00102$:
	mov	dptr,#_BankProjectileInit_i_10000_43
	movx	a,@dptr
	mov	b,#0x02
	mul	ab
	add	a, #_projectile_info
	mov	dpl,a
	mov	a,#(_projectile_info >> 8)
	addc	a, b
	mov	dph,a
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
	mov	dptr,#_projectile_sprites
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankProjectileInit_i_10000_43
	movx	a,@dptr
	mov	b,#0x14
	mul	ab
	add	a, r5
	mov	r5,a
	mov	a,r6
	addc	a, b
	mov	r6,a
	mov	a,#0x12
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#_BankProjectileInit_i_10000_43
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	movx	a,@dptr
	mov	r7,a
	cjne	r7,#0x08,00113$
00113$:
	jc	00102$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:21: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'BankProjectileSpawn'
;------------------------------------------------------------
;owner         Allocated to stack - bp +1 +2 
;sloc0         Allocated to stack - bp +3 +3 
;sloc1         Allocated to stack - bp +6 +3 
;sloc2         Allocated to stack - bp +9 +3 
;sloc3         Allocated to stack - bp +12 +4 
;sloc4         Allocated to stack - bp +16 +4 
;i             Allocated with name '_BankProjectileSpawn_i_10000_47'
;dx            Allocated with name '_BankProjectileSpawn_dx_10000_47'
;dy            Allocated with name '_BankProjectileSpawn_dy_10000_47'
;den           Allocated with name '_BankProjectileSpawn_den_10000_47'
;p             Allocated with name '_BankProjectileSpawn_p_10000_47'
;v             Allocated with name '_BankProjectileSpawn_v_10000_47'
;header        Allocated with name '_BankProjectileSpawn_header_10000_47'
;------------------------------------------------------------
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:22: void BankProjectileSpawn(uint16_t owner) __sdcccall(1)
;	-----------------------------------------
;	 function BankProjectileSpawn
;	-----------------------------------------
_BankProjectileSpawn:
	push	bp
	mov	bp,sp
	push	dpl
	push	dph
	mov	a,sp
	add	a,#0x11
	mov	sp,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:29: for(i=0;i<8;++i)if(!projectile_sprites[i].health)break;
	mov	dptr,#_BankProjectileSpawn_i_10000_47
	clr	a
	movx	@dptr,a
00110$:
	mov	dptr,#_projectile_sprites
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	dptr,#_BankProjectileSpawn_i_10000_47
	movx	a,@dptr
	mov	r2,a
	mov	b,#0x14
	mul	ab
	xch	a,r0
	mov	a,bp
	add	a,#0x06
	xch	a,r0
	add	a, @r0
	mov	r7,a
	inc	r0
	mov	a,@r0
	addc	a, b
	mov	r5,a
	inc	r0
	mov	ar6,@r0
	mov	a,#0x12
	add	a, r7
	mov	r4,a
	clr	a
	addc	a, r5
	mov	r5,a
	mov	dpl,r4
	mov	dph,r5
	mov	b,r6
	lcall	__gptrget
	mov	r4,a
	inc	dptr
	lcall	__gptrget
	orl	a,r4
	jz	00103$
	mov	dptr,#_BankProjectileSpawn_i_10000_47
	mov	a,r2
	inc	a
	movx	@dptr,a
	movx	a,@dptr
	mov	r5,a
	cjne	r5,#0x08,00177$
00177$:
	jc	00110$
00103$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:30: if(i==8){++projectile_info[6];return;}
	mov	dptr,#_BankProjectileSpawn_i_10000_47
	movx	a,@dptr
	mov	r5,a
	cjne	r5,#0x08,00105$
	mov	dptr,#(_projectile_info + 0x000c)
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	r3
	cjne	r3,#0x00,00181$
	inc	r4
00181$:
	mov	dptr,#(_projectile_info + 0x000c)
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	ljmp	00112$
00105$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:31: p=projectile_states+i;v=projectile_sprites+i;
	mov	dptr,#_projectile_states
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,r5
	mov	b,#0x10
	mul	ab
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	add	a, r2
	movx	@dptr,a
	mov	a,r3
	addc	a, b
	inc	dptr
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	mov	a,r5
	mov	b,#0x14
	mul	ab
	xch	a,r0
	mov	a,bp
	add	a,#0x06
	xch	a,r0
	add	a, @r0
	mov	r3,a
	inc	r0
	mov	a,@r0
	addc	a, b
	mov	r4,a
	inc	r0
	mov	ar5,@r0
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:32: v->x=actor_things[owner].x;v->y=actor_things[owner].y;
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	@r0,ar3
	inc	r0
	mov	@r0,ar4
	inc	r0
	mov	@r0,ar5
	mov	dptr,#_actor_things
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	push	ar5
	push	ar4
	push	ar3
	mov	r0,bp
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	dptr,#0x0014
	lcall	__mulint
	mov	r6, dpl
	mov	r7, dph
	dec	sp
	dec	sp
	pop	ar3
	pop	ar4
	pop	ar5
	mov	a,r6
	add	a, r3
	mov	r2,a
	mov	a,r7
	addc	a, r4
	mov	r4,a
	mov	dpl,r2
	mov	dph,r4
	mov	b,r5
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r4
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	a,#0x02
	add	a, r3
	mov	@r0,a
	clr	a
	addc	a, r4
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar5
	mov	dptr,#_actor_things
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r6
	add	a, r2
	mov	r2,a
	mov	a,r7
	addc	a, r4
	mov	r4,a
	mov	a,#0x02
	add	a, r2
	mov	r2,a
	clr	a
	addc	a, r4
	mov	r4,a
	mov	dpl,r2
	mov	dph,r4
	mov	b,r5
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r4
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:33: v->floor=actor_things[owner].floor+32;
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	a,#0x10
	add	a, r3
	mov	@r0,a
	clr	a
	addc	a, r4
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar5
	mov	dptr,#_actor_things
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r6
	add	a, r2
	mov	r6,a
	mov	a,r7
	addc	a, r4
	mov	r7,a
	mov	ar3,r5
	mov	a,#0x10
	add	a, r6
	mov	r6,a
	clr	a
	addc	a, r7
	mov	r7,a
	mov	dpl,r6
	mov	dph,r7
	mov	b,r3
	lcall	__gptrget
	mov	r6,a
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	mov	a,#0x20
	add	a, r6
	mov	r6,a
	clr	a
	addc	a, r7
	mov	r7,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r6
	lcall	__gptrput
	inc	dptr
	mov	a,r7
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:34: p->x=(int32_t)v->x*65536L;p->y=(int32_t)v->y*65536L;
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	rlc	a
	subb	a,acc
	mov	ar7,r3
	mov	ar4,r2
	clr	a
	mov	r2,a
	mov	r3,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	inc	dptr
	mov	a,r4
	lcall	__gptrput
	inc	dptr
	mov	a,r7
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	a,#0x04
	add	a, r5
	mov	@r0,a
	clr	a
	addc	a, r6
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar7
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,#0x02
	add	a, r2
	mov	r2,a
	clr	a
	addc	a, r3
	mov	r3,a
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	rlc	a
	subb	a,acc
	mov	ar7,r3
	mov	ar4,r2
	clr	a
	mov	r2,a
	mov	r3,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	inc	dptr
	mov	a,r4
	lcall	__gptrput
	inc	dptr
	mov	a,r7
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:35: dx=(motion_state.x>>16)-v->x;dy=(motion_state.y>>16)-v->y;
	mov	dptr,#_motion_state
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	xch	a,r6
	xch	a,r7
	xch	a,r6
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	mov	ar2,@r0
	inc	r0
	mov	ar4,@r0
	inc	r0
	mov	ar5,@r0
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	dpl,r2
	mov	dph,r4
	mov	b,r5
	lcall	__gptrget
	mov	@r0,a
	inc	dptr
	lcall	__gptrget
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	ar2,@r0
	inc	r0
	mov	ar5,@r0
	mov	a,r7
	clr	c
	subb	a,r2
	mov	r4,a
	mov	a,r6
	subb	a,r5
	mov	r5,a
	mov	dptr,#_BankProjectileSpawn_dx_10000_47
	mov	a,r4
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_motion_state + 0x0004)
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	@r0,ar6
	inc	r0
	mov	@r0,ar7
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	mov	a,#0x02
	add	a, @r0
	mov	r3,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar7,@r0
	mov	dpl,r3
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r3,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	ar7,@r0
	inc	r0
	mov	ar2,@r0
	mov	a,r7
	clr	c
	subb	a,r3
	mov	r7,a
	mov	a,r2
	subb	a,r6
	mov	r6,a
	mov	dptr,#_BankProjectileSpawn_dy_10000_47
	mov	a,r7
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:36: den=dx<0 ? -dx:dx;if((dy<0 ? -dy:dy)>den)den=dy<0 ? -dy:dy;
	mov	ar3,r5
	mov	a,r3
	jnb	acc.7,00114$
	clr	c
	clr	a
	subb	a,r4
	mov	r2,a
	clr	a
	subb	a,r5
	mov	r3,a
	sjmp	00115$
00114$:
	mov	ar2,r4
	mov	ar3,r5
00115$:
	push	ar4
	push	ar5
	mov	dptr,#_BankProjectileSpawn_den_10000_47
	mov	a,r2
	movx	@dptr,a
	mov	a,r3
	inc	dptr
	movx	@dptr,a
	mov	ar5,r6
	mov	a,r5
	pop	ar5
	pop	ar4
	jnb	acc.7,00116$
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	clr	c
	clr	a
	subb	a,r7
	mov	@r0,a
	clr	a
	subb	a,r6
	inc	r0
	mov	@r0,a
	sjmp	00117$
00116$:
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	mov	@r0,ar7
	inc	r0
	mov	@r0,ar6
00117$:
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	clr	c
	mov	a,r2
	subb	a,@r0
	mov	a,r3
	xrl	a,#0x80
	inc	r0
	mov	b,@r0
	xrl	b,#0x80
	subb	a,b
	jnc	00107$
	mov	ar3,r6
	mov	a,r3
	jnb	acc.7,00118$
	clr	c
	clr	a
	subb	a,r7
	mov	r2,a
	clr	a
	subb	a,r6
	mov	r3,a
	sjmp	00119$
00118$:
	mov	ar2,r7
	mov	ar3,r6
00119$:
	mov	dptr,#_BankProjectileSpawn_den_10000_47
	mov	a,r2
	movx	@dptr,a
	mov	a,r3
	inc	dptr
	movx	@dptr,a
00107$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:37: if(!den)return;
	mov	dptr,#_BankProjectileSpawn_den_10000_47
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	dptr,#_BankProjectileSpawn_den_10000_47
	movx	a,@dptr
	mov	b,a
	inc	dptr
	movx	a,@dptr
	orl	a,b
	jnz	00109$
	ljmp	00112$
00109$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:38: p->vx=FixedDiv(dx,den)>>5;p->vy=FixedDiv(dy,den)>>5;
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	a,#0x08
	add	a, r2
	mov	@r0,a
	clr	a
	addc	a, r3
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar7
	mov	a,bp
	add	a,#0x09
	mov	r0,a
	mov	a,bp
	add	a,#0x0c
	mov	r1,a
	mov	a,@r0
	mov	@r1,a
	inc	r0
	mov	a,@r0
	inc	r1
	mov	@r1,a
	mov	a,@r0
	rlc	a
	subb	a,acc
	inc	r1
	mov	@r1,a
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	a,r5
	rlc	a
	subb	a,acc
	mov	r6,a
	mov	r7,a
	mov	a,bp
	add	a,#0x0c
	mov	r0,a
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	dpl, r4
	mov	dph, r5
	mov	b, r6
	mov	a, r7
	lcall	_FixedDiv
	mov	r4, dpl
	mov	r5, dph
	mov	r6, b
	mov	r7, a
	mov	a,sp
	add	a,#0xfc
	mov	sp,a
	mov	a,r5
	swap	a
	rr	a
	xch	a,r4
	swap	a
	rr	a
	anl	a,#0x07
	xrl	a,r4
	xch	a,r4
	anl	a,#0x07
	xch	a,r4
	xrl	a,r4
	xch	a,r4
	mov	r5,a
	mov	a,r6
	swap	a
	rr	a
	anl	a,#0xf8
	orl	a,r5
	mov	r5,a
	mov	a,r7
	swap	a
	rr	a
	xch	a,r6
	swap	a
	rr	a
	anl	a,#0x07
	xrl	a,r6
	xch	a,r6
	anl	a,#0x07
	xch	a,r6
	xrl	a,r6
	xch	a,r6
	jnb	acc.2,00187$
	orl	a,#0xf8
00187$:
	mov	a,bp
	add	a,#0x06
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r4
	lcall	__gptrput
	inc	dptr
	mov	a,r5
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x0c
	mov	r0,a
	mov	a,#0x0a
	add	a, r5
	mov	@r0,a
	clr	a
	addc	a, r6
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar7
	mov	dptr,#_BankProjectileSpawn_den_10000_47
	mov	a,bp
	add	a,#0x10
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	movx	a,@dptr
	rlc	a
	subb	a,acc
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,a
	mov	dptr,#_BankProjectileSpawn_dy_10000_47
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	movx	a,@dptr
	rlc	a
	subb	a,acc
	mov	r6,a
	mov	r7,a
	mov	a,bp
	add	a,#0x10
	mov	r0,a
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	dpl, r4
	mov	dph, r5
	mov	b, r6
	mov	a, r7
	lcall	_FixedDiv
	mov	r4, dpl
	mov	r5, dph
	mov	r6, b
	mov	r7, a
	mov	a,sp
	add	a,#0xfc
	mov	sp,a
	mov	a,r5
	swap	a
	rr	a
	xch	a,r4
	swap	a
	rr	a
	anl	a,#0x07
	xrl	a,r4
	xch	a,r4
	anl	a,#0x07
	xch	a,r4
	xrl	a,r4
	xch	a,r4
	mov	r5,a
	mov	a,r6
	swap	a
	rr	a
	anl	a,#0xf8
	orl	a,r5
	mov	r5,a
	mov	a,r7
	swap	a
	rr	a
	xch	a,r6
	swap	a
	rr	a
	anl	a,#0x07
	xrl	a,r6
	xch	a,r6
	anl	a,#0x07
	xch	a,r6
	xrl	a,r6
	xch	a,r6
	jnb	acc.2,00188$
	orl	a,#0xf8
00188$:
	mov	a,bp
	add	a,#0x0c
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r4
	lcall	__gptrput
	inc	dptr
	mov	a,r5
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:39: p->age=0;p->owner=owner;
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_p_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0e
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	r0,bp
	inc	r0
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,@r0
	lcall	__gptrput
	inc	dptr
	inc	r0
	mov	a,@r0
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:40: header=DdrPointer(0xD0010UL);v->kind=header[2];
	mov	dptr,#0x0010
	mov	b, #0x0d
	clr	a
	lcall	_DdrPointer
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
	mov	dptr,#_BankProjectileSpawn_header_10000_47
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,#0x06
	add	a, r2
	mov	r2,a
	clr	a
	addc	a, r3
	mov	r3,a
	mov	a,#0x04
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r5,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	mov	a,r5
	lcall	__gptrput
	inc	dptr
	mov	a,r6
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:41: v->angle=v->tics=0;v->frame=0;v->awake=1;v->health=1;
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x04
	add	a, r5
	mov	r2,a
	clr	a
	addc	a, r6
	mov	r3,a
	mov	ar4,r7
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0e
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0f
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x01
	lcall	__gptrput
	mov	dptr,#_BankProjectileSpawn_v_10000_47
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x12
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x01
	lcall	__gptrput
	inc	dptr
	clr	a
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:42: ++projectile_info[0];
	mov	dptr,#_projectile_info
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00189$
	inc	r7
00189$:
	mov	dptr,#_projectile_info
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
00112$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:43: }
	mov	sp,bp
	pop	bp
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'BankProjectileTick'
;------------------------------------------------------------
;sloc0         Allocated to stack - bp +1 +3 
;sloc1         Allocated to stack - bp +4 +3 
;sloc2         Allocated to stack - bp +7 +4 
;sloc3         Allocated to stack - bp +11 +4 
;i             Allocated with name '_BankProjectileTick_i_10000_55'
;step          Allocated with name '_BankProjectileTick_step_10000_55'
;x             Allocated with name '_BankProjectileTick_x_10000_55'
;y             Allocated with name '_BankProjectileTick_y_10000_55'
;nx            Allocated with name '_BankProjectileTick_nx_10000_55'
;ny            Allocated with name '_BankProjectileTick_ny_10000_55'
;dx            Allocated with name '_BankProjectileTick_dx_10000_55'
;dy            Allocated with name '_BankProjectileTick_dy_10000_55'
;p             Allocated with name '_BankProjectileTick_p_10000_55'
;v             Allocated with name '_BankProjectileTick_v_10000_55'
;------------------------------------------------------------
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:44: void BankProjectileTick(void) __sdcccall(1)
;	-----------------------------------------
;	 function BankProjectileTick
;	-----------------------------------------
_BankProjectileTick:
	push	bp
	mov	a,sp
	mov	bp,a
	add	a,#0x0e
	mov	sp,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:50: projectile_info[7]=0;
	mov	dptr,#(_projectile_info + 0x000e)
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:51: for(i=0;i<8;++i) {
	mov	dptr,#_BankProjectileTick_i_10000_55
	movx	@dptr,a
00125$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:52: v=projectile_sprites+i;if(!v->health)continue;
	mov	dptr,#_BankProjectileTick_i_10000_55
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_projectile_sprites
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	mov	a,r7
	mov	b,#0x14
	mul	ab
	add	a, r4
	mov	r4,a
	mov	a,r5
	addc	a, b
	mov	r5,a
	mov	dptr,#_BankProjectileTick_v_10000_55
	mov	a,r4
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,#0x12
	add	a, r4
	mov	r4,a
	clr	a
	addc	a, r5
	mov	r5,a
	mov	dpl,r4
	mov	dph,r5
	mov	b,r6
	lcall	__gptrget
	mov	r4,a
	inc	dptr
	lcall	__gptrget
	orl	a,r4
	jnz	00226$
	ljmp	00121$
00226$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:53: ++projectile_info[7];p=projectile_states+i;
	mov	dptr,#(_projectile_info + 0x000e)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00227$
	inc	r7
00227$:
	mov	dptr,#(_projectile_info + 0x000e)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dptr,#_BankProjectileTick_i_10000_55
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_projectile_states
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	mov	a,r7
	mov	b,#0x10
	mul	ab
	add	a, r4
	mov	r7,a
	mov	a,r5
	addc	a, b
	mov	r5,a
	mov	dptr,#_BankProjectileTick_p_10000_55
	mov	a,r7
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:54: if(v->awake==2) {
	mov	dptr,#_BankProjectileTick_v_10000_55
	mov	r0,bp
	inc	r0
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	r0,bp
	inc	r0
	mov	a,#0x0f
	add	a, @r0
	mov	r4,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r3,a
	inc	r0
	mov	ar2,@r0
	mov	dpl,r4
	mov	dph,r3
	mov	b,r2
	lcall	__gptrget
	mov	r3,a
	cjne	r3,#0x02,00228$
	sjmp	00229$
00228$:
	ljmp	00108$
00229$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:55: if(++v->tics>=4){v->tics=0;if(++v->frame>4)v->health=0;}
	mov	r0,bp
	inc	r0
	mov	a,#0x0c
	add	a, @r0
	mov	r7,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar5,@r0
	mov	dpl,r7
	mov	dph,r6
	mov	b,r5
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	inc	r2
	cjne	r2,#0x00,00230$
	inc	r3
00230$:
	mov	dpl,r7
	mov	dph,r6
	mov	b,r5
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	clr	c
	mov	a,r2
	subb	a,#0x04
	mov	a,r3
	subb	a,#0x00
	jnc	00231$
	ljmp	00121$
00231$:
	mov	dptr,#_BankProjectileTick_v_10000_55
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x0c
	add	a, @r0
	mov	@r0,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x0e
	add	a, @r0
	mov	r7,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar5,@r0
	mov	dpl,r7
	mov	dph,r6
	mov	b,r5
	lcall	__gptrget
	mov	r3,a
	inc	r3
	mov	dpl,r7
	mov	dph,r6
	mov	b,r5
	mov	a,r3
	lcall	__gptrput
	add	a,#0xff - 0x04
	jc	00232$
	ljmp	00121$
00232$:
	mov	dptr,#_BankProjectileTick_v_10000_55
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x12
	add	a, @r0
	mov	@r0,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:56: continue;
	ljmp	00121$
00108$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:58: if(++p->age>105){v->health=0;++projectile_info[5];continue;}
	mov	a,#0x0c
	add	a, r7
	mov	r7,a
	clr	a
	addc	a, r5
	mov	r5,a
	mov	dpl,r7
	mov	dph,r5
	mov	b,r6
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	inc	r2
	cjne	r2,#0x00,00233$
	inc	r3
00233$:
	mov	dpl,r7
	mov	dph,r5
	mov	b,r6
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	clr	c
	mov	a,#0x69
	subb	a,r2
	clr	a
	subb	a,r3
	jnc	00110$
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x12
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#(_projectile_info + 0x000a)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00235$
	inc	r7
00235$:
	mov	dptr,#(_projectile_info + 0x000a)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	ljmp	00121$
00110$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:59: v->frame=(p->age>>2)&1;
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0e
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	ar4,r7
	mov	dptr,#_BankProjectileTick_p_10000_55
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r2
	mov	r2,a
	clr	a
	addc	a, r3
	mov	r3,a
	mov	dpl,r2
	mov	dph,r3
	mov	b,r7
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	a,r2
	rr	a
	rr	a
	anl	a,#0x01
	mov	dpl,r5
	mov	dph,r6
	mov	b,r4
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:60: for(step=0;step<4;++step) {
	mov	dptr,#_BankProjectileTick_step_10000_55
	clr	a
	movx	@dptr,a
00123$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:61: x=p->x>>16;y=p->y>>16;
	mov	dptr,#_BankProjectileTick_p_10000_55
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	r1,bp
	inc	r1
	mov	a,@r0
	mov	@r1,a
	inc	r0
	mov	a,@r0
	inc	r1
	mov	@r1,a
	inc	r0
	mov	a,@r0
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	r0,bp
	inc	r0
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	mov	ar3,r6
	mov	ar5,r7
	mov	dptr,#_BankProjectileTick_x_10000_55
	mov	a,r3
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x04
	add	a, @r0
	mov	r5,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar7,@r0
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	mov	ar5,r7
	mov	ar6,r3
	mov	dptr,#_BankProjectileTick_y_10000_55
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:62: p->x+=(int32_t)p->vx*64L;p->y+=(int32_t)p->vy*64L;
	mov	r0,bp
	inc	r0
	mov	a,bp
	add	a,#0x07
	mov	r1,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x08
	add	a, @r0
	mov	r2,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar7,@r0
	mov	dpl,r2
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	rlc	a
	subb	a,acc
	mov	r7,a
	anl	a,#0x03
	mov	c,acc.0
	xch	a,r7
	rrc	a
	xch	a,r7
	rrc	a
	mov	c,acc.0
	xch	a,r7
	rrc	a
	xch	a,r7
	rrc	a
	xch	a,r7
	mov	r5,a
	mov	a,r6
	rr	a
	rr	a
	anl	a,#0x3f
	orl	a,r7
	mov	r7,a
	mov	a,r6
	anl	a,#0x03
	mov	c,acc.0
	xch	a,r2
	rrc	a
	xch	a,r2
	rrc	a
	mov	c,acc.0
	xch	a,r2
	rrc	a
	xch	a,r2
	rrc	a
	xch	a,r2
	mov	r6,a
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	mov	a,r2
	add	a, @r0
	mov	r2,a
	mov	a,r6
	inc	r0
	addc	a, @r0
	mov	r6,a
	mov	a,r7
	inc	r0
	addc	a, @r0
	mov	r7,a
	mov	a,r5
	inc	r0
	addc	a, @r0
	mov	r5,a
	mov	r0,bp
	inc	r0
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r6
	lcall	__gptrput
	inc	dptr
	mov	a,r7
	lcall	__gptrput
	inc	dptr
	mov	a,r5
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_p_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x04
	add	a, r5
	mov	@r0,a
	clr	a
	addc	a, r6
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar7
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,bp
	add	a,#0x0b
	mov	r1,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
	inc	dptr
	lcall	__gptrget
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	a,#0x0a
	add	a, r5
	mov	r2,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r2
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	rlc	a
	subb	a,acc
	mov	r7,a
	anl	a,#0x03
	mov	c,acc.0
	xch	a,r7
	rrc	a
	xch	a,r7
	rrc	a
	mov	c,acc.0
	xch	a,r7
	rrc	a
	xch	a,r7
	rrc	a
	xch	a,r7
	mov	r5,a
	mov	a,r6
	rr	a
	rr	a
	anl	a,#0x3f
	orl	a,r7
	mov	r7,a
	mov	a,r6
	anl	a,#0x03
	mov	c,acc.0
	xch	a,r2
	rrc	a
	xch	a,r2
	rrc	a
	mov	c,acc.0
	xch	a,r2
	rrc	a
	xch	a,r2
	rrc	a
	xch	a,r2
	mov	r6,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	a,r2
	add	a, @r0
	mov	r2,a
	mov	a,r6
	inc	r0
	addc	a, @r0
	mov	r6,a
	mov	a,r7
	inc	r0
	addc	a, @r0
	mov	r7,a
	mov	a,r5
	inc	r0
	addc	a, @r0
	mov	r5,a
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r6
	lcall	__gptrput
	inc	dptr
	mov	a,r7
	lcall	__gptrput
	inc	dptr
	mov	a,r5
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:63: nx=p->x>>16;ny=p->y>>16;
	mov	dptr,#_BankProjectileTick_p_10000_55
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	ar2,@r0
	inc	r0
	mov	ar3,@r0
	inc	r0
	mov	ar7,@r0
	mov	dpl,r2
	mov	dph,r3
	mov	b,r7
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	mov	ar2,r7
	mov	ar3,r6
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	mov	@r0,ar2
	inc	r0
	mov	@r0,ar3
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	mov	dptr,#_BankProjectileTick_nx_10000_55
	mov	a,@r0
	movx	@dptr,a
	inc	r0
	mov	a,@r0
	inc	dptr
	movx	@dptr,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	a,#0x04
	add	a, @r0
	mov	r7,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r5,a
	inc	r0
	mov	ar6,@r0
	mov	dpl,r7
	mov	dph,r5
	mov	b,r6
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	mov	ar3,r6
	mov	ar5,r7
	mov	dptr,#_BankProjectileTick_ny_10000_55
	mov	a,r3
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:64: if(!MotionVisible(x,y,nx,ny,v->floor)) {
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x10
	add	a, r2
	mov	r2,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r2
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	mov	dptr,#_BankProjectileTick_x_10000_55
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	push	ar2
	push	ar4
	push	ar3
	push	ar5
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	dptr,#_BankProjectileTick_y_10000_55
	movx	a,@dptr
	push	acc
	inc	dptr
	movx	a,@dptr
	push	acc
	mov	dpl, r6
	mov	dph, r7
	lcall	_MotionVisible
	mov	r7, dpl
	mov	a,sp
	add	a,#0xf8
	mov	sp,a
	mov	a,r7
	jnz	00112$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:65: v->awake=2;v->frame=2;v->tics=0;++projectile_info[2];break;
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0f
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x02
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0e
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x02
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#(_projectile_info + 0x0004)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00237$
	inc	r7
00237$:
	mov	dptr,#(_projectile_info + 0x0004)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	ljmp	00121$
00112$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:67: v->x=nx;v->y=ny;++projectile_info[1];
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankProjectileTick_nx_10000_55
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x02
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dptr,#_BankProjectileTick_ny_10000_55
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r3,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,r2
	lcall	__gptrput
	inc	dptr
	mov	a,r3
	lcall	__gptrput
	mov	dptr,#(_projectile_info + 0x0002)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00238$
	inc	r7
00238$:
	mov	dptr,#(_projectile_info + 0x0002)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:68: dx=nx-(int16_t)(motion_state.x>>16);dy=ny-(int16_t)(motion_state.y>>16);
	mov	dptr,#_motion_state
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	ar3,r6
	mov	ar5,r7
	mov	dptr,#_BankProjectileTick_nx_10000_55
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	a,r6
	clr	c
	subb	a,r3
	mov	@r0,a
	mov	a,r7
	subb	a,r5
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	dptr,#_BankProjectileTick_dx_10000_55
	mov	a,@r0
	movx	@dptr,a
	inc	r0
	mov	a,@r0
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_motion_state + 0x0004)
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	ar2,r5
	mov	ar3,r7
	mov	dptr,#_BankProjectileTick_ny_10000_55
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,r6
	clr	c
	subb	a,r2
	mov	r6,a
	mov	a,r7
	subb	a,r3
	mov	r7,a
	mov	dptr,#_BankProjectileTick_dy_10000_55
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:69: if(dx>=-20 && dx<=20 && dy>=-20 && dy<=20 && v->floor>=motion_state.floor && v->floor<motion_state.floor+56) {
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	clr	c
	mov	a,@r0
	subb	a,#0xec
	inc	r0
	mov	a,@r0
	xrl	a,#0x80
	subb	a,#0x7f
	jnc	00239$
	ljmp	00124$
00239$:
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	ar3,@r0
	inc	r0
	mov	ar5,@r0
	clr	c
	mov	a,#0x14
	subb	a,r3
	mov	a,#(0x00 ^ 0x80)
	mov	b,r5
	xrl	b,#0x80
	subb	a,b
	jnc	00240$
	ljmp	00124$
00240$:
	clr	c
	mov	a,r6
	subb	a,#0xec
	mov	a,r7
	xrl	a,#0x80
	subb	a,#0x7f
	jnc	00241$
	ljmp	00124$
00241$:
	clr	c
	mov	a,#0x14
	subb	a,r6
	mov	a,#(0x00 ^ 0x80)
	mov	b,r7
	xrl	b,#0x80
	subb	a,b
	jnc	00242$
	ljmp	00124$
00242$:
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x10
	add	a, r6
	mov	r6,a
	clr	a
	addc	a, r5
	mov	r5,a
	mov	dpl,r6
	mov	dph,r5
	mov	b,r7
	lcall	__gptrget
	mov	r6,a
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	mov	dptr,#(_motion_state + 0x000c)
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	clr	c
	mov	a,r6
	subb	a,r3
	mov	a,r7
	xrl	a,#0x80
	mov	b,r5
	xrl	b,#0x80
	subb	a,b
	jnc	00243$
	ljmp	00124$
00243$:
	mov	dptr,#(_motion_state + 0x000c)
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,#0x38
	add	a, r3
	mov	r3,a
	clr	a
	addc	a, r5
	mov	r5,a
	clr	c
	mov	a,r6
	subb	a,r3
	mov	a,r7
	xrl	a,#0x80
	mov	b,r5
	xrl	b,#0x80
	subb	a,b
	jnc	00124$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:70: PlayerDamage(10);v->awake=2;v->frame=2;v->tics=0;++projectile_info[3];break;
	mov	dpl, #0x0a
	lcall	_PlayerDamage
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0f
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x02
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0e
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,#0x02
	lcall	__gptrput
	mov	dptr,#_BankProjectileTick_v_10000_55
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#(_projectile_info + 0x0006)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00245$
	inc	r7
00245$:
	mov	dptr,#(_projectile_info + 0x0006)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	sjmp	00121$
00124$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:60: for(step=0;step<4;++step) {
	mov	dptr,#_BankProjectileTick_step_10000_55
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	movx	a,@dptr
	mov	r7,a
	cjne	r7,#0x04,00246$
00246$:
	jnc	00247$
	ljmp	00123$
00247$:
00121$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:51: for(i=0;i<8;++i) {
	mov	dptr,#_BankProjectileTick_i_10000_55
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	movx	a,@dptr
	mov	r7,a
	cjne	r7,#0x08,00248$
00248$:
	jnc	00249$
	ljmp	00125$
00249$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:74: }
	mov	sp,bp
	pop	bp
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'BankPickupInit'
;------------------------------------------------------------
;sloc0         Allocated to stack - bp +1 +3 
;sloc1         Allocated to stack - bp +4 +3 
;sloc2         Allocated to stack - bp +4 +3 
;sloc3         Allocated to stack - bp +7 +4 
;i             Allocated with name '_BankPickupInit_i_10000_73'
;header        Allocated with name '_BankPickupInit_header_10000_73'
;ceiling       Allocated with name '_BankPickupInit_ceiling_10000_73'
;------------------------------------------------------------
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:81: void BankPickupInit(void) __sdcccall(1)
;	-----------------------------------------
;	 function BankPickupInit
;	-----------------------------------------
_BankPickupInit:
	push	bp
	mov	a,sp
	mov	bp,a
	add	a,#0x0a
	mov	sp,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:85: header=DdrPointer(DOOM_PICKUP_HEADER_BASE);pickup_count=header[0];
	mov	dptr,#0x8010
	mov	b, #0x0d
	clr	a
	lcall	_DdrPointer
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
	mov	dptr,#_BankPickupInit_header_10000_73
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r5,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	mov	dptr,#_pickup_count
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:86: if(pickup_count>DOOM_PICKUP_MAX){ddr_fault=6;pickup_count=0;return;}
	clr	c
	mov	a,#0x80
	subb	a,r5
	clr	a
	subb	a,r6
	jnc	00102$
	mov	dptr,#_ddr_fault
	mov	a,#0x06
	movx	@dptr,a
	mov	dptr,#_pickup_count
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
	ljmp	00112$
00102$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:87: pickup_things=actor_things+actor_count+8;
	mov	dptr,#_actor_things
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	push	ar7
	push	ar6
	push	ar5
	mov	dptr,#_actor_count
	movx	a,@dptr
	push	acc
	inc	dptr
	movx	a,@dptr
	push	acc
	mov	dptr,#0x0014
	lcall	__mulint
	mov	r3, dpl
	mov	r4, dph
	dec	sp
	dec	sp
	pop	ar5
	pop	ar6
	pop	ar7
	mov	a,r3
	add	a, r5
	mov	r5,a
	mov	a,r4
	addc	a, r6
	mov	r6,a
	mov	dptr,#_pickup_things
	mov	a,#0xa0
	add	a, r5
	movx	@dptr,a
	clr	a
	addc	a, r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:88: header=DdrPointer(0xD0010UL);header[1]=actor_count+8+pickup_count;
	mov	dptr,#0x0010
	mov	b, #0x0d
	clr	a
	lcall	_DdrPointer
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
	mov	dptr,#_BankPickupInit_header_10000_73
	mov	a,r5
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	a,#0x02
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dptr,#_actor_count
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,#0x08
	add	a, r3
	mov	r3,a
	clr	a
	addc	a, r4
	mov	r4,a
	mov	dptr,#_pickup_count
	movx	a,@dptr
	mov	r1,a
	inc	dptr
	movx	a,@dptr
	mov	r2,a
	mov	a,r1
	add	a, r3
	mov	r1,a
	mov	a,r2
	addc	a, r4
	mov	r2,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	mov	a,r1
	lcall	__gptrput
	inc	dptr
	mov	a,r2
	lcall	__gptrput
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:89: for(i=0;i<4;++i)pickup_info[i]=0;
	mov	dptr,#_BankPickupInit_i_10000_73
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
00107$:
	mov	dptr,#_BankPickupInit_i_10000_73
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,r6
	add	a,r6
	mov	r6,a
	mov	a,r7
	rlc	a
	mov	r7,a
	mov	a,r6
	add	a, #_pickup_info
	mov	dpl,a
	mov	a,r7
	addc	a, #(_pickup_info >> 8)
	mov	dph,a
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
	mov	dptr,#_BankPickupInit_i_10000_73
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	inc	dptr
	movx	a,@dptr
	addc	a, #0x00
	movx	@dptr,a
	mov	dptr,#_BankPickupInit_i_10000_73
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	clr	c
	mov	a,r6
	subb	a,#0x04
	mov	a,r7
	subb	a,#0x00
	jc	00107$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:90: for(i=0;i<pickup_count;++i) {
	mov	dptr,#_BankPickupInit_i_10000_73
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
00110$:
	mov	dptr,#_BankPickupInit_i_10000_73
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_pickup_count
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	clr	c
	mov	a,r6
	subb	a,r4
	mov	a,r7
	subb	a,r5
	jc	00158$
	ljmp	00112$
00158$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:91: if(pickup_things[i].tics>=DOOM_PICKUP_RULES){ddr_fault=6;return;}
	mov	dptr,#_pickup_things
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	push	ar5
	push	ar4
	push	ar3
	push	ar6
	push	ar7
	mov	dptr,#0x0014
	lcall	__mulint
	mov	r6, dpl
	mov	r7, dph
	dec	sp
	dec	sp
	pop	ar3
	pop	ar4
	pop	ar5
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,r6
	add	a, r3
	mov	@r0,a
	mov	a,r7
	addc	a, r4
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar5
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x0c
	add	a, @r0
	mov	r2,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r3,a
	inc	r0
	mov	ar4,@r0
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	clr	c
	mov	a,r2
	subb	a,#0x0b
	mov	a,r3
	subb	a,#0x00
	jc	00105$
	mov	dptr,#_ddr_fault
	mov	a,#0x06
	movx	@dptr,a
	ljmp	00112$
00105$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:92: MotionSectorAt((int32_t)pickup_things[i].x*65536L,(int32_t)pickup_things[i].y*65536L,&pickup_things[i].floor,&ceiling);
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	r1,bp
	inc	r1
	mov	a,#0x10
	add	a, @r0
	mov	@r1,a
	clr	a
	inc	r0
	addc	a, @r0
	inc	r1
	mov	@r1,a
	inc	r0
	mov	a,@r0
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	a,#0x02
	add	a, @r0
	mov	r7,a
	clr	a
	inc	r0
	addc	a, @r0
	mov	r6,a
	inc	r0
	mov	ar5,@r0
	mov	dpl,r7
	mov	dph,r6
	mov	b,r5
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	rlc	a
	subb	a,acc
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	inc	r0
	inc	r0
	inc	r0
	mov	@r0,ar3
	dec	r0
	mov	@r0,ar2
	dec	r0
	dec	r0
	mov	@r0,#0x00
	inc	r0
	mov	@r0,#0x00
	mov	a,bp
	add	a,#0x04
	mov	r0,a
	mov	ar5,@r0
	inc	r0
	mov	ar6,@r0
	inc	r0
	mov	ar7,@r0
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r5,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	rlc	a
	subb	a,acc
	mov	ar3,r6
	mov	ar7,r5
	clr	a
	mov	r5,a
	mov	r6,a
	mov	a,#_BankPickupInit_ceiling_10000_73
	push	acc
	mov	a,#(_BankPickupInit_ceiling_10000_73 >> 8)
	push	acc
	clr	a
	push	acc
	mov	r0,bp
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	a,bp
	add	a,#0x07
	mov	r0,a
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	dpl, r5
	mov	dph, r6
	mov	b, r7
	mov	a, r3
	lcall	_MotionSectorAt
	mov	a,sp
	add	a,#0xf6
	mov	sp,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:90: for(i=0;i<pickup_count;++i) {
	mov	dptr,#_BankPickupInit_i_10000_73
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	inc	dptr
	movx	a,@dptr
	addc	a, #0x00
	movx	@dptr,a
	ljmp	00110$
00112$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:94: }
	mov	sp,bp
	pop	bp
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'BankPickupTick'
;------------------------------------------------------------
;sloc0         Allocated to stack - bp +1 +2 
;sloc1         Allocated to stack - bp +3 +2 
;sloc2         Allocated to stack - bp +5 +3 
;sloc3         Allocated to stack - bp +8 +3 
;sloc4         Allocated to stack - bp +11 +2 
;sloc5         Allocated to stack - bp +13 +3 
;i             Allocated with name '_BankPickupTick_i_10000_82'
;amount        Allocated with name '_BankPickupTick_amount_10000_82'
;value         Allocated with name '_BankPickupTick_value_10000_82'
;cap           Allocated with name '_BankPickupTick_cap_10000_82'
;x             Allocated with name '_BankPickupTick_x_10000_82'
;y             Allocated with name '_BankPickupTick_y_10000_82'
;dx            Allocated with name '_BankPickupTick_dx_10000_82'
;dy            Allocated with name '_BankPickupTick_dy_10000_82'
;dz            Allocated with name '_BankPickupTick_dz_10000_82'
;p             Allocated with name '_BankPickupTick_p_10000_82'
;------------------------------------------------------------
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:95: void BankPickupTick(void) __sdcccall(1)
;	-----------------------------------------
;	 function BankPickupTick
;	-----------------------------------------
_BankPickupTick:
	push	bp
	mov	a,sp
	mov	bp,a
	add	a,#0x0f
	mov	sp,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:100: if(!combat.health)return;
	mov	dptr,#_combat
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	orl	a,r6
	jnz	00102$
	ljmp	00135$
00102$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:101: if(pickup_info[3])--pickup_info[3];
	mov	dptr,#(_pickup_info + 0x0006)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	orl	a,r6
	jz	00104$
	mov	dptr,#(_pickup_info + 0x0006)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	dec	r6
	cjne	r6,#0xff,00301$
	dec	r7
00301$:
	mov	dptr,#(_pickup_info + 0x0006)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
00104$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:102: x=motion_state.x>>16;y=motion_state.y>>16;
	mov	dptr,#_motion_state
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	ar4,r6
	mov	ar5,r7
	mov	dptr,#_BankPickupTick_x_10000_82
	mov	a,r4
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_motion_state + 0x0004)
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	ar4,r6
	mov	ar5,r7
	mov	dptr,#_BankPickupTick_y_10000_82
	mov	a,r4
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:103: for(i=0;i<pickup_count;++i) {
	mov	dptr,#_BankPickupTick_i_10000_82
	clr	a
	movx	@dptr,a
	inc	dptr
	movx	@dptr,a
00134$:
	mov	dptr,#_BankPickupTick_i_10000_82
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_pickup_count
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	clr	c
	mov	a,r6
	subb	a,r4
	mov	a,r7
	subb	a,r5
	jc	00302$
	ljmp	00135$
00302$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:104: p=pickup_things+i;if(!p->health)continue;
	mov	dptr,#_pickup_things
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	push	ar5
	push	ar4
	push	ar3
	push	ar6
	push	ar7
	mov	dptr,#0x0014
	lcall	__mulint
	mov	r6, dpl
	mov	r7, dph
	dec	sp
	dec	sp
	pop	ar3
	pop	ar4
	pop	ar5
	mov	a,r6
	add	a, r3
	mov	r6,a
	mov	a,r7
	addc	a, r4
	mov	r7,a
	mov	dptr,#_BankPickupTick_p_10000_82
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	a,r5
	inc	dptr
	movx	@dptr,a
	mov	a,#0x12
	add	a, r6
	mov	r2,a
	clr	a
	addc	a, r7
	mov	r3,a
	mov	ar4,r5
	mov	dpl,r2
	mov	dph,r3
	mov	b,r4
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	orl	a,r2
	jnz	00303$
	ljmp	00131$
00303$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:105: dx=p->x-x;dy=p->y-y;dz=p->floor-motion_state.floor;
	mov	a,bp
	add	a,#0x08
	mov	r0,a
	mov	@r0,ar6
	inc	r0
	mov	@r0,ar7
	inc	r0
	mov	@r0,ar5
	mov	a,bp
	add	a,#0x08
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r4,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	mov	dptr,#_BankPickupTick_x_10000_82
	mov	r0,bp
	inc	r0
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	r0,bp
	inc	r0
	mov	a,bp
	add	a,#0x03
	mov	r1,a
	mov	a,r4
	clr	c
	subb	a,@r0
	mov	@r1,a
	mov	a,r3
	inc	r0
	subb	a,@r0
	inc	r1
	mov	@r1,a
;	freeAsmop r1 1
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	dptr,#_BankPickupTick_dx_10000_82
	mov	a,@r0
	movx	@dptr,a
	inc	r0
	mov	a,@r0
	inc	dptr
	movx	@dptr,a
	mov	a,bp
	add	a,#0x05
	mov	r0,a
	mov	a,#0x02
	add	a, r6
	mov	@r0,a
	clr	a
	addc	a, r7
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar5
	mov	a,bp
	add	a,#0x05
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r3,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	mov	dptr,#_BankPickupTick_y_10000_82
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	movx	a,@dptr
	mov	@r0,a
	inc	dptr
	movx	a,@dptr
	inc	r0
	mov	@r0,a
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	a,r3
	clr	c
	subb	a,@r0
	mov	r3,a
	mov	a,r4
	inc	r0
	subb	a,@r0
	mov	r4,a
	mov	dptr,#_BankPickupTick_dy_10000_82
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	mov	a,#0x10
	add	a, r6
	mov	@r0,a
	clr	a
	addc	a, r7
	inc	r0
	mov	@r0,a
	inc	r0
	mov	@r0,ar5
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r7,a
	inc	dptr
	lcall	__gptrget
	mov	r2,a
	mov	dptr,#(_motion_state + 0x000c)
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	mov	a,r7
	clr	c
	subb	a,r5
	mov	r7,a
	mov	a,r2
	subb	a,r6
	mov	r6,a
	mov	dptr,#_BankPickupTick_dz_10000_82
	mov	a,r7
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:106: if(dx< -DOOM_PICKUP_RADIUS || dx>DOOM_PICKUP_RADIUS || dy< -DOOM_PICKUP_RADIUS || dy>DOOM_PICKUP_RADIUS || dz< -8 || dz>56)continue;
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	clr	c
	mov	a,@r0
	subb	a,#0xec
	inc	r0
	mov	a,@r0
	xrl	a,#0x80
	subb	a,#0x7f
	jnc	00304$
	ljmp	00131$
00304$:
	mov	a,bp
	add	a,#0x03
	mov	r0,a
	mov	ar2,@r0
	inc	r0
	mov	ar5,@r0
	clr	c
	mov	a,#0x14
	subb	a,r2
	mov	a,#(0x00 ^ 0x80)
	mov	b,r5
	xrl	b,#0x80
	subb	a,b
	jnc	00305$
	ljmp	00131$
00305$:
	clr	c
	mov	a,r3
	subb	a,#0xec
	mov	a,r4
	xrl	a,#0x80
	subb	a,#0x7f
	jnc	00306$
	ljmp	00131$
00306$:
	clr	c
	mov	a,#0x14
	subb	a,r3
	mov	a,#(0x00 ^ 0x80)
	mov	b,r4
	xrl	b,#0x80
	subb	a,b
	jnc	00307$
	ljmp	00131$
00307$:
	clr	c
	mov	a,r7
	subb	a,#0xf8
	mov	a,r6
	xrl	a,#0x80
	subb	a,#0x7f
	jnc	00308$
	ljmp	00131$
00308$:
	clr	c
	mov	a,#0x38
	subb	a,r7
	mov	a,#(0x00 ^ 0x80)
	mov	b,r6
	xrl	b,#0x80
	subb	a,b
	jnc	00309$
	ljmp	00131$
00309$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:107: if(!MotionVisible(x,y,p->x,p->y,p->floor+4))continue;
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r6,a
	inc	dptr
	lcall	__gptrget
	mov	r7,a
	mov	a,#0x04
	add	a, r6
	mov	r6,a
	clr	a
	addc	a, r7
	mov	r7,a
	mov	a,bp
	add	a,#0x05
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r4,a
	inc	dptr
	lcall	__gptrget
	mov	r5,a
	mov	a,bp
	add	a,#0x08
	mov	r0,a
	mov	dpl,@r0
	inc	r0
	mov	dph,@r0
	inc	r0
	mov	b,@r0
	lcall	__gptrget
	mov	r2,a
	inc	dptr
	lcall	__gptrget
	mov	r3,a
	push	ar6
	push	ar7
	push	ar4
	push	ar5
	push	ar2
	push	ar3
	mov	a,bp
	add	a,#0x0b
	mov	r0,a
	mov	a,@r0
	push	acc
	inc	r0
	mov	a,@r0
	push	acc
	mov	r0,bp
	inc	r0
	mov	dpl, @r0
	inc	r0
	mov	dph, @r0
	lcall	_MotionVisible
	mov	r7, dpl
	mov	a,sp
	add	a,#0xf8
	mov	sp,a
	mov	a,r7
	jnz	00310$
	ljmp	00131$
00310$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:108: if(p->tics>=DOOM_FIRST_KEY_RULE) {
	mov	dptr,#_BankPickupTick_p_10000_82
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r3,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	mov	@r0,ar3
	inc	r0
	mov	@r0,ar4
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	clr	c
	mov	a,@r0
	subb	a,#0x05
	inc	r0
	mov	a,@r0
	subb	a,#0x00
	jc	00129$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:109: amount=1U<<(p->tics-DOOM_FIRST_KEY_RULE);
	mov	a,r3
	add	a,#0xfb
	mov	b, a
	inc	b
	mov	r3,#0x01
	mov	r4,#0x00
	sjmp	00313$
00312$:
	mov	a,r3
	add	a,r3
	mov	r3,a
	mov	a,r4
	rlc	a
	mov	r4,a
00313$:
	djnz	b,00312$
	mov	ar7,r3
	mov	ar6,r4
	mov	dptr,#_BankPickupTick_amount_10000_82
	mov	a,r7
	movx	@dptr,a
	mov	a,r6
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:110: if(key_info[0]&amount)continue;
	mov	dptr,#_key_info
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,r7
	anl	ar2,a
	mov	a,r6
	anl	ar4,a
	mov	a,r2
	orl	a,r4
	jz	00314$
	ljmp	00131$
00314$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:111: key_info[0]|=amount;
	mov	dptr,#_key_info
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,r7
	orl	ar3,a
	mov	a,r6
	orl	ar4,a
	mov	dptr,#_key_info
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	ljmp	00130$
00129$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:113: if(p->tics<3) {
	mov	a,bp
	add	a,#0x0d
	mov	r0,a
	clr	c
	mov	a,@r0
	subb	a,#0x03
	inc	r0
	mov	a,@r0
	subb	a,#0x00
	jnc	00119$
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:114: value=combat.health;cap=p->tics==2 ? DOOM_BONUS_HEALTH:DOOM_NORMAL_HEALTH;
	mov	dptr,#_combat
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	dptr,#_BankPickupTick_value_10000_82
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r3,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	cjne	r3,#0x02,00137$
	cjne	r4,#0x00,00137$
	mov	r4,#0xc8
	sjmp	00138$
00137$:
	mov	r4,#0x64
00138$:
	mov	dptr,#_BankPickupTick_cap_10000_82
	mov	a,r4
	movx	@dptr,a
	clr	a
	inc	dptr
	movx	@dptr,a
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:115: amount=p->tics==0 ? 10:(p->tics==1 ? 25:1);
	mov	dptr,#_BankPickupTick_p_10000_82
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r2,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	a,#0x0c
	add	a, r3
	mov	r3,a
	clr	a
	addc	a, r2
	mov	r2,a
	mov	dpl,r3
	mov	dph,r2
	mov	b,r4
	lcall	__gptrget
	mov	r3,a
	inc	dptr
	lcall	__gptrget
	mov	r4,a
	orl	a,r3
	jnz	00139$
	mov	r2,#0x0a
	sjmp	00140$
00139$:
	cjne	r3,#0x01,00141$
	cjne	r4,#0x00,00141$
	mov	r4,#0x19
	sjmp	00142$
00141$:
	mov	r4,#0x01
00142$:
	mov	ar2,r4
00140$:
	mov	dptr,#_BankPickupTick_amount_10000_82
	mov	a,r2
	movx	@dptr,a
	clr	a
	inc	dptr
	movx	@dptr,a
	sjmp	00120$
00119$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:116: } else {value=combat.ammo;cap=DOOM_MAX_BULLETS;amount=p->tics==3 ? 10:50;}
	mov	dptr,#(_combat + 0x0002)
	movx	a,@dptr
	mov	r3,a
	inc	dptr
	movx	a,@dptr
	mov	r4,a
	mov	dptr,#_BankPickupTick_value_10000_82
	mov	a,r3
	movx	@dptr,a
	mov	a,r4
	inc	dptr
	movx	@dptr,a
	mov	dptr,#_BankPickupTick_cap_10000_82
	mov	a,#0xc8
	movx	@dptr,a
	clr	a
	inc	dptr
	movx	@dptr,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r5,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	cjne	r5,#0x03,00143$
	cjne	r6,#0x00,00143$
	mov	r7,#0x0a
	sjmp	00144$
00143$:
	mov	r7,#0x32
00144$:
	mov	dptr,#_BankPickupTick_amount_10000_82
	mov	a,r7
	movx	@dptr,a
	clr	a
	inc	dptr
	movx	@dptr,a
00120$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:117: if(value>=cap)continue;
	mov	dptr,#_BankPickupTick_value_10000_82
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankPickupTick_cap_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	clr	c
	mov	a,r6
	subb	a,r4
	mov	a,r7
	subb	a,r5
	jc	00323$
	ljmp	00131$
00323$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:118: if(amount>cap-value)amount=cap-value;
	mov	a,r4
	clr	c
	subb	a,r6
	mov	r2,a
	mov	a,r5
	subb	a,r7
	mov	r3,a
	push	ar4
	push	ar5
	mov	dptr,#_BankPickupTick_amount_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	clr	c
	mov	a,r2
	subb	a,r4
	mov	a,r3
	subb	a,r5
	pop	ar5
	pop	ar4
	jnc	00124$
	mov	dptr,#_BankPickupTick_amount_10000_82
	mov	a,r4
	clr	c
	subb	a,r6
	movx	@dptr,a
	mov	a,r5
	subb	a,r7
	inc	dptr
	movx	@dptr,a
00124$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:119: if(p->tics<3){combat.health+=amount;pickup_info[1]+=amount;}
	mov	dptr,#_BankPickupTick_p_10000_82
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x0c
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r5,a
	inc	dptr
	lcall	__gptrget
	mov	r6,a
	clr	c
	mov	a,r5
	subb	a,#0x03
	mov	a,r6
	subb	a,#0x00
	jnc	00126$
	mov	dptr,#_combat
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankPickupTick_amount_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r4
	add	a, r6
	mov	r6,a
	mov	a,r5
	addc	a, r7
	mov	r7,a
	mov	dptr,#_combat
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_pickup_info + 0x0002)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankPickupTick_amount_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r4
	add	a, r6
	mov	r6,a
	mov	a,r5
	addc	a, r7
	mov	r7,a
	mov	dptr,#(_pickup_info + 0x0002)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	sjmp	00130$
00126$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:120: else {combat.ammo+=amount;pickup_info[2]+=amount;}
	mov	dptr,#(_combat + 0x0002)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankPickupTick_amount_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r4
	add	a, r6
	mov	r6,a
	mov	a,r5
	addc	a, r7
	mov	r7,a
	mov	dptr,#(_combat + 0x0002)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_pickup_info + 0x0004)
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	dptr,#_BankPickupTick_amount_10000_82
	movx	a,@dptr
	mov	r4,a
	inc	dptr
	movx	a,@dptr
	mov	r5,a
	mov	a,r4
	add	a, r6
	mov	r6,a
	mov	a,r5
	addc	a, r7
	mov	r7,a
	mov	dptr,#(_pickup_info + 0x0004)
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
00130$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:122: p->health=0;++pickup_info[0];pickup_info[3]=DOOM_PICKUP_FLASH_TICKS;
	mov	dptr,#_BankPickupTick_p_10000_82
	movx	a,@dptr
	mov	r5,a
	inc	dptr
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	mov	a,#0x12
	add	a, r5
	mov	r5,a
	clr	a
	addc	a, r6
	mov	r6,a
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	clr	a
	lcall	__gptrput
	inc	dptr
	lcall	__gptrput
	mov	dptr,#_pickup_info
	movx	a,@dptr
	mov	r6,a
	inc	dptr
	movx	a,@dptr
	mov	r7,a
	inc	r6
	cjne	r6,#0x00,00326$
	inc	r7
00326$:
	mov	dptr,#_pickup_info
	mov	a,r6
	movx	@dptr,a
	mov	a,r7
	inc	dptr
	movx	@dptr,a
	mov	dptr,#(_pickup_info + 0x0006)
	mov	a,#0x05
	movx	@dptr,a
	clr	a
	inc	dptr
	movx	@dptr,a
00131$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:103: for(i=0;i<pickup_count;++i) {
	mov	dptr,#_BankPickupTick_i_10000_82
	movx	a,@dptr
	add	a, #0x01
	movx	@dptr,a
	inc	dptr
	movx	a,@dptr
	addc	a, #0x00
	movx	@dptr,a
	ljmp	00134$
00135$:
;	/workspace/scratch/5690bd253bc6/doom-exit-repo/tmp/doom-exit/projectile_engine.c:124: }
	mov	sp,bp
	pop	bp
	ret
	.area CSEG    (CODE)
	.area CONST   (CODE)
	.area XINIT   (CODE)
	.area CABS    (ABS,CODE)
