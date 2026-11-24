#include "../fw/doom/graphics.h"
__xdata __at(DOOM_GRAPHICS_MAILBOX) graphics_mailbox_t graphics;
volatile __xdata __at(0xF600) uint8_t status;
volatile __xdata __at(0xF620) uint8_t op;
__xdata uint16_t doom_column_target,doom_column_frac,doom_column_step;
__xdata uint8_t doom_column_count;
void BankDrawPlane(void);
void main(void)
{
    DdrInit();status=0xA5;
    for(;;)if(op){BankDrawPlane();DdrFlush();status=ddr_fault ? ddr_fault:0xA5;op=0;}
}
