/* Real C pointer arithmetic and the C maths ABI, executed as 8051 opcodes. */
#include "../fw/doom/platform.h"
#ifdef DOOM_STACK
void DdrWriteStack(uint32_t address, uint8_t value);
#define DdrWrite DdrWriteStack
#endif
typedef struct { int32_t x, y; uint16_t next; uint8_t mark; } node_t;
static __xdata node_t *unused_xdata_type;
static __xdata uint8_t near_buffer[16];
static __code const uint8_t code_buffer[] = {0x13, 0x37, 0x51, 0xD0};
static __xdata uint32_t texture_hits;
volatile __xdata __at(0xF600) uint8_t platform_status[16];
volatile __xdata __at(0xF620) int32_t platform_a;
volatile __xdata __at(0xF624) int32_t platform_b;
volatile __xdata __at(0xF628) int32_t platform_result;
volatile __xdata __at(0xF62C) uint8_t platform_op;
__xdata uint16_t doom_column_target, doom_column_frac, doom_column_step;
__xdata uint8_t doom_column_count;

static void fail(uint8_t reason) { platform_status[1] = reason; }
void main(void)
{
    uint16_t i;
    uint8_t bank;
    node_t *nodes;
    uint8_t *generic;
    unused_xdata_type = 0;
    platform_status[0] = 1;
    DdrInit();
    for (bank = 1; bank != 8; ++bank) {
        nodes = DdrPointer(((uint32_t)bank << 16) + 0x210);
        for (i = 0; i != 48; ++i) {
            nodes[i].x = FixedMul((int32_t)(i + bank) << 16, 0x18000L);
            nodes[i].y = FixedDiv(-((int32_t)(i + 1) << 16), 0x30000L);
            nodes[i].next = i + bank;
            nodes[i].mark = i ^ bank;
        }
    }
    /* Collision-heavy bank traversal forces dirty eviction and reload. */
    DdrFlush();
    for (i = 0; i != 48; ++i) for (bank = 1; bank != 8; ++bank) {
        nodes = DdrPointer(((uint32_t)bank << 16) + 0x210);
        if (nodes[i].x != FixedMul((int32_t)(i + bank) << 16, 0x18000L)) fail(1);
        if (nodes[i].y != FixedDiv(-((int32_t)(i + 1) << 16), 0x30000L)) fail(2);
        if (nodes[i].next != i + bank || nodes[i].mark != (uint8_t)(i ^ bank)) fail(3);
    }
    generic = near_buffer;
    for (i = 0; i != 16; ++i) generic[i] = i ^ 0xAA;
    for (i = 0; i != 16; ++i) if (generic[i] != (i ^ 0xAA)) fail(4);
    generic = (uint8_t *)code_buffer;
    if (generic[1] != 0x37 || generic[3] != 0xD0) fail(5);
    /* Explicit addresses still cover all 32 MiB beyond the 4 MiB pointer heap. */
    DdrWrite(0x1FFFFFFUL, 0x51);
    DdrWrite(0x3FFFFFUL, 0xD0);
    DdrFlush();
    if (DdrRead(0x1FFFFFFUL) != 0x51 || DdrRead(0x3FFFFFUL) != 0xD0) fail(6);
    /* Offset zero is reserved because SDCC tests only the offset for null. */
    nodes = DdrPointer(0x3F0000UL);
    if (nodes || ddr_fault != 4) fail(8);
    ddr_fault = 0;
    nodes = DdrPointer(0x3F0010UL);
    if (!nodes) fail(8);
    nodes->next = 0xBEEF;
    if (nodes->next != 0xBEEF || nodes+1 <= nodes) fail(9);
    /* Generic hot hits must distinguish all nine physical bank bits. */
    DdrWrite(0x3F0010UL, 0xEF);
    DdrWrite(0x13F0010UL, 0x63);
    if (*(uint8_t *)DdrPointer(0x3F0010UL) != 0xEF) fail(10);
    if (DdrRead(0x13F0010UL) != 0x63) fail(10);
    /* Full-line overwrites invalidate their own dirty line, while preserving
     * an unrelated dirty line that collides at the same cache index. */
    for (i = 0; i != 16; ++i) ddr_burst_buffer[i] = i ^ 0x75;
    DdrWrite(0x100010UL, 0xAA);
    DdrWriteBurst(0x100010UL);
    if (DdrRead(0x100010UL) != 0x75) fail(11);
    DdrWrite(0x100010UL, 0xBB);
    DdrWriteBurst(0x110010UL);
    if (DdrRead(0x100010UL) != 0xBB) fail(12);
    DdrFlush();
    if (DdrRead(0x11001FUL) != (15 ^ 0x75)) fail(12);
    DdrWriteBurst(0x110011UL);
    if (ddr_fault != 3) fail(13);
    ddr_fault = 0;
    if (ddr_fault) fail(7);
    /* Chunk boundaries, negative/overflowing 16-bit texture phase, and staged
     * texture/colormap SRAM. Python independently checks the DDR bytes. */
    for (i = 0; i != 128; ++i) DdrWrite(0x180010UL + i, i ^ 0x5A);
    DdrFlush();
    DdrLoadColumn(0x180010UL);
    texture_hits = ddr_hits;
    DdrLoadColumn(0x180010UL);
    if (texture_hits != ddr_hits) fail(17);
    for (i = 0; i != 128; ++i)
        if (((__xdata uint8_t *)DOOM_TEXTURE_COLUMN_BASE)[i] != (i ^ 0x5A)) fail(17);
    for (i = 0; i != 128; ++i) ((__xdata uint8_t *)DOOM_TEXTURE_COLUMN_BASE)[i] = i ^ 0x55;
    for (i = 0; i != 256; ++i) ((__xdata uint8_t *)DOOM_COLORMAP_BASE)[i] = i ^ 0xAA;
    doom_draw_address = 0x16000FUL;
    doom_draw_count = 35;
    doom_draw_color = 7;
    DdrDrawColumn(0);
    doom_draw_address = 0x16100FUL;
    doom_draw_count = 35;
    doom_column_frac = 0xF123;
    doom_column_step = 0x1ABC;
    DdrDrawColumn(1);
    if (doom_column_frac != (uint16_t)(0xF123UL + 35UL * 0x1ABCUL)) fail(18);
    DdrFlush();
    DdrWrite(DOOM_INDEXED_BASE, 0xAA);
    DdrFlush();
    DdrClearFrame();
    if (DdrRead(DOOM_INDEXED_BASE)) fail(14);
    DdrWrite(DOOM_INDEXED_BASE + 3, 9);
    if (DdrRead(DOOM_INDEXED_BASE + 2048)) fail(14);
    if (DdrRead(DOOM_INDEXED_BASE + 3) != 9) fail(14);
    for (i = 0; i != 16; ++i) ddr_burst_buffer[i] = 42;
    DdrWriteBurst(DOOM_INDEXED_BASE + 48);
    if (DdrRead(DOOM_INDEXED_BASE + 48) != 42) fail(15);
    DdrFlush();
    DdrWrite(0x17000FUL, 0xC5);
    DdrClearFrame();
    if (DdrRead(DOOM_INDEXED_BASE + 3) || DdrRead(DOOM_INDEXED_BASE + 48)) fail(16);
    if (DdrRead(0x17000FUL) != 0xC5 || DdrRead(0x16000FUL) != 7) fail(16);
    DdrFlush();
    platform_status[2] = (uint8_t)ddr_hits;
    platform_status[3] = (uint8_t)ddr_misses;
    platform_status[0] = 0xA5;
    for (;;) {
        if (platform_op == 1) { platform_result = FixedMul(platform_a, platform_b); platform_op = 0; }
        if (platform_op == 2) { platform_result = FixedDiv(platform_a, platform_b); platform_op = 0; }
        if (platform_op == 3) { platform_result = DoomReciprocalStep((uint32_t)platform_a); platform_op = 0; }
    }
}
