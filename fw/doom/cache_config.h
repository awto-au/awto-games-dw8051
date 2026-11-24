/* Fixed MCU SRAM pages shared by C misses and the DW8051 hot cache path.
 * Dynamic XRAM is linked below E000h. DDR still uses MCU_DC transactions. */
#ifndef DOOM_CACHE_CONFIG_H
#define DOOM_CACHE_CONFIG_H
#define DOOM_CACHE_LINES          128
#define DOOM_CACHE_DATA_BASE      0xE000
#define DOOM_CACHE_OFFSETS_BASE   0xE800
#define DOOM_CACHE_BANKS_BASE     0xE900
#define DOOM_CACHE_PALETTE_BASE   0xEA00
#define DOOM_CACHE_BURST_BASE     0xED00
#define DOOM_TEXTURE_COLUMN_BASE  0xED80
#define DOOM_COLORMAP_BASE        0xEE00
#define DOOM_TILE_BASE            0xEF00
#define DOOM_FRAME_BITMAP_BASE    0xF000
#define DOOM_FRAME_BITMAP_BYTES   256
#define DOOM_TEXTURE_COLUMN_SIZE  128
#define DOOM_TILE_SIZE            256
#define DOOM_RGB_BLOCK_SIZE       48
#define DOOM_CACHE_VALID          0x4000
#define DOOM_CACHE_DIRTY          0x8000
#define DOOM_CACHE_BANK_MASK      0x01FF
#define DOOM_DDR_BURST_BYTES      16
#define DOOM_DDR_CAPACITY         0x02000000
#define DOOM_DDR_CMD_WRITE        0x80
#define DOOM_DDR_CMD_READ         0xA0
#define DOOM_DDR_READY            1
#define DOOM_DDR_POLL_LIMIT       1024
#define DOOM_DDR_READ_ATTEMPTS    3
#define DOOM_PALETTE_BYTES        768
#define DOOM_RASTER_BASE          0x01F00000
#ifndef DOOM_RASTER_PITCH
#define DOOM_RASTER_PITCH         192
#endif
#ifndef DOOM_VIEW_WIDTH
#define DOOM_VIEW_WIDTH           60
#endif
#ifndef DOOM_VIEW_HEIGHT
#define DOOM_VIEW_HEIGHT          128
#endif
#define DOOM_INDEXED_BASE         0x000F0010
#define DOOM_SFR_CKCON            0x8E
#define DOOM_SFR_MPAGE            0x92
#define DOOM_MOVX_MASK            7
#define DOOM_MOVX_DEFAULT         0
#endif
