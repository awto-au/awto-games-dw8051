/* Cache metadata and block operations. Native DW8051 assembly implements
 * cache misses, dirty eviction and the real MCU_DC port transactions. */
#include "platform.h"
uint8_t DdrStore(uint8_t index);
void DdrWriteRaw(uint32_t addr);
__xdata __at(DOOM_CACHE_DATA_BASE) uint8_t ddr_cache_data[DOOM_CACHE_LINES * DOOM_DDR_BURST_BYTES];
__xdata __at(DOOM_CACHE_OFFSETS_BASE) uint16_t ddr_cache_offsets[DOOM_CACHE_LINES];
__xdata __at(DOOM_CACHE_BANKS_BASE) uint16_t ddr_cache_banks[DOOM_CACHE_LINES];
__xdata __at(DOOM_CACHE_BURST_BASE) uint8_t ddr_burst_buffer[DOOM_RGB_BLOCK_SIZE];
__xdata __at(DOOM_FRAME_BITMAP_BASE) uint8_t doom_frame_bitmap[DOOM_FRAME_BITMAP_BYTES];
__xdata uint8_t doom_frame_active;
__xdata uint8_t ddr_fault;
__xdata uint32_t doom_draw_address;
__xdata uint8_t doom_draw_count, doom_draw_color;
/* Explicit cache API calls only; hot generic-pointer hits avoid counters. */
__xdata uint32_t ddr_hits, ddr_misses;
__xdata uint16_t doom_burst_source;
__xdata uint32_t doom_colormap_address, doom_texture_address;

void DdrInit(void)
{
    uint8_t i;
    ddr_fault = 0;
    doom_frame_active = 0;
    ddr_hits = ddr_misses = 0;
    doom_colormap_address = 0;
    doom_texture_address = 0;
    for (i = 0; i != DOOM_CACHE_LINES; ++i) ddr_cache_banks[i] = 0;
}

void DdrFlush(void)
{
    uint8_t i;
    for (i = 0; i != DOOM_CACHE_LINES; ++i) if (!DdrStore(i)) return;
}

void DdrWriteBurst(uint32_t addr)
{
    doom_burst_source = DOOM_CACHE_BURST_BASE;
    DdrWriteRaw(addr);
}

void *DdrPointer(uint32_t addr)
{
    union { uint8_t bytes[3]; void *ptr; } p;
    if (addr < 0x10000UL || addr >= 0x400000UL || !(uint16_t)addr) { ddr_fault = 4; return 0; }
    p.bytes[0] = addr;
    p.bytes[1] = addr >> 8;
    p.bytes[2] = addr >> 16;
    return p.ptr;
}
