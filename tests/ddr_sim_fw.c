/* Compile the existing DDR draw/verify firmware unchanged, then execute it on
 * the DW8051 fast core. No scaler output, IRQ or video input is required. */
typedef unsigned char BYTE;
typedef unsigned short WORD;
#define _ON 1
#define _OFF 0
#define _AWTO_FREEZE _ON
#define AWTO_DRW_HOST
#define GET_OSD_FREEZE_STATUS() 1
#include "../fw/sdk/Project/Header/AwtoRegs.h"
#define DRW_RD(reg) (*(volatile __xdata BYTE *)(reg))
#define DRW_WR(reg, val) (*(volatile __xdata BYTE *)(reg) = (val))
#define DRW_FEED() do { } while (0)
static unsigned long test_ms;
/* Only a bound for timeout/retry tests, not an elapsed-time measurement. */
static unsigned long AwtoMs(void) { return test_ms++; }
#include "../fw/test/ddr_draw.c"
StAwtoDraw g_stAwtoDraw;
StAwtoAddr g_stAwtoAddr;
volatile __xdata __at(0xF600) BYTE test_result[8];

void main(void)
{
    test_result[0] = 1;
    g_stAwtoDraw.usX = 0;
    g_stAwtoDraw.usY = 0;
    g_stAwtoDraw.ucGo = AWTO_DRW_OP_FIGURE;
    AwtoDrwPoll();
    test_result[1] = g_stAwtoDraw.ucState;
    /* Last 8 KiB of 32 MiB, independent of the visible figure at address zero. */
    g_stAwtoAddr.ulBlk0 = 16380UL;
    g_stAwtoAddr.ulBlocks = 4;
    g_stAwtoAddr.ulSeed = 0xF5B4A162UL;
    g_stAwtoAddr.usStride = 1;
    g_stAwtoAddr.ucSwap = 1;
    g_stAwtoAddr.ucRetry = 2;
    g_stAwtoDraw.ucGo = AWTO_DRW_OP_ADDR_FILL;
    AwtoDrwPoll();
    test_result[2] = g_stAwtoDraw.ucState;
    g_stAwtoDraw.ucGo = AWTO_DRW_OP_ADDR_VERIFY;
    AwtoDrwPoll();
    test_result[3] = g_stAwtoDraw.ucState;
    test_result[4] = g_stAwtoAddr.ulBad != 0;
    test_result[5] = g_stAwtoAddr.ulChecked == 512UL;
    test_result[6] = g_stAwtoAddr.ulTmo != 0;
    test_result[0] = 0xA5;
    for (;;) { }
}
