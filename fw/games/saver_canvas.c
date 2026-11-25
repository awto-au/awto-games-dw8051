#include <stdint.h>
#include <string.h>
#include "UserCommonInclude.h"
#include "AwtoApps.h"
#define OSD_NO_FLUSH
#include "../../ddc/tools/osd_lines/osd_lines.c"
#include "arcade.h"

// Shared by Scope 2 and Asteroids (one runs at a time): the osd_lines renderer, the band canvas, the 1-bit tile upload.

#define SC_BANDS                                2                   // size of the shared band canvas (Asteroids draws into it, Scope 2 uses the tile buffer)
#define SC_ROWS                                 12
#define SC_BAND_ROWS                            (SC_ROWS / SC_BANDS)
#define ARC_CHAR1_B0                            0x40                // 1-bit char command; B0[4:0] = glyph width
#define ARC_ID_HI_SHIFT                         5                   // B0[5] = glyph id bit 8
#define ARC_ID_LO_MASK                          0xFF

__xdata uint8_t g_aucScPix[OSD_BITMAP_BYTES(1, SC_BAND_ROWS)];
__xdata uint8_t g_aucScDirty[OSD_DIRTY_BYTES(1, SC_BAND_ROWS)];
__xdata osd_canvas g_scCv;

void AwtoScTile(WORD usAddr, BYTE __xdata *pucB)                    // a 1-bit tile, turned in place for Rotate 180 (AwtoAppGlyph)
{
    AwtoAppGlyph(usAddr, pucB, OSD_TILE_BYTES);
}

void ArcOsdMap1(BYTE ucCols, BYTE ucRows, BYTE ucAttr)             // 1-bit map: char command per cell, glyph id = cell index, one attribute (fg << 4 | bg)
{
    WORD usI;
    WORD usCells = (WORD)ucCols * ucRows;
    WORD usFontBase = ucRows + 1 + usCells;                         // row commands + end word, then one char command per cell

    ScalerOsdAddrSet(_OSD_SRAM, _OSD_BYTEALL, ucRows + 1, _OSD_WITHOUT_DB);
    for(usI = 0; usI < usCells; usI++)
    {
        AWTO_OSD_PORT(ARC_CHAR1_B0 | OSD_TILE_W | (BYTE)((usI >> 8) << ARC_ID_HI_SHIFT));
        AWTO_OSD_PORT((BYTE)(usI & ARC_ID_LO_MASK));
        AWTO_OSD_PORT(ucAttr);
    }
    SET_OSD_MAPA_COL_MAX(ucCols);
    ScalerOsdSramBaseAddressSet(_OSD_A, AWTO_OSD_ZERO, ucRows + 1, usFontBase);
}

void ArcKey(BYTE ucKey, BYTE ucEv)
{
    if((ucKey == ARC_KEY_QUIT) && (ucEv == AWTO_KEV_PRESS))
    {
        AwtoAppStop();
    }
}
