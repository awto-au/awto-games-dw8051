/* Native graphics-bank mailbox. Fixed SRAM is outside cache and door pages. */
#ifndef DOOM_GRAPHICS_H
#define DOOM_GRAPHICS_H
#include "platform.h"
#define DOOM_GRAPHICS_MAILBOX 0xF300
#define DOOM_FLAT_DIRECTORY 0x00140010UL
#define DOOM_FLAT_PIXELS 0x00800010UL
#define DOOM_SKY_PIXELS 0x00160010UL
#define DOOM_SKY_WIDTH 256
#define DOOM_PLANE_PROJECTION 128
#define DOOM_FLAT_SIDE 64
#define DOOM_SKY_FLAG 1
typedef struct {
    int32_t x,y,z,cosine,sine,height;
    uint32_t angle;
    int16_t pic,light;
    uint8_t column,first,last,flags;
} graphics_mailbox_t;
extern __xdata __at(DOOM_GRAPHICS_MAILBOX) graphics_mailbox_t graphics;
void R_DrawPlaneBank(void);
static uint16_t GraphicsDivide(uint16_t value,uint16_t divisor)
{
    uint16_t result=0,remainder=0;uint8_t bit=16;
    do {remainder=(remainder<<1)|(value>>15);value<<=1;result<<=1;
        if(remainder>=divisor){remainder-=divisor;result|=1;}
    } while(--bit);
    return result;
}
#endif
