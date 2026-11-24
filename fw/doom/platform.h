/* Native SDCC/DW8051 platform. All DDR traffic uses MCU_DC port A. */
#ifndef DOOM_PLATFORM_H
#define DOOM_PLATFORM_H
#include <stdint.h>
#include "cache_config.h"

int32_t FixedMul(int32_t a, int32_t b) __sdcccall(0);
int32_t FixedDiv(int32_t a, int32_t b) __sdcccall(0);

/* Generic pointer tags 1..63 are reserved by this executable for DDR.
 * Objects must not cross a 64 KiB boundary or include offset zero. Normal SDCC XDATA, IDATA,
 * PDATA and CODE tags retain their usual meanings. No hardware MMU is used.
 * These routines and the pointer bridge are non-reentrant; no interrupts. */
void *DdrPointer(uint32_t address);
void DdrInit(void);
void DdrFlush(void);
uint8_t DdrRead(uint32_t address);
void DdrWrite(uint32_t address, uint8_t value) __sdcccall(1);
void DdrWriteBurst(uint32_t address);
void DdrPresentRow(uint32_t address);
void DdrPresentFrame(void);
void DdrDrawColumn(uint8_t textured);
uint16_t DoomReciprocalStep(uint32_t denominator);
extern __xdata uint32_t doom_draw_address;
extern __xdata uint8_t doom_draw_count, doom_draw_color;
void DdrClearFrame(void);
void DdrLoadColumn(uint32_t address);
void DdrLoadColorMap(uint32_t address);
void DdrGatherTile(uint32_t address);
uint8_t __xdata *DdrMapWrite(uint32_t address);
const uint8_t __xdata *DdrMapRead(uint32_t address);
extern __xdata __at(DOOM_CACHE_BURST_BASE) uint8_t ddr_burst_buffer[DOOM_RGB_BLOCK_SIZE];
/* One-long register ABI packs source pointer in the low word and target in
 * the high word, avoiding mixed stack/register argument conventions. */
void DoomCopy16(uint32_t pointers);
void DoomTranspose16(uint32_t pointers);
void DoomWrite16(uint16_t source);
void DoomExpand16(uint16_t source);
void DoomFillChunk(uint32_t count_color_target);
uint16_t DoomShadeChunk(void);
extern __xdata uint16_t doom_column_target, doom_column_frac, doom_column_step;
extern __xdata uint8_t doom_column_count;
extern __xdata uint8_t ddr_fault;
extern __xdata uint32_t ddr_hits, ddr_misses;

#endif
