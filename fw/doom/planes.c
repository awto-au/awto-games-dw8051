/* Perspective plane and cylindrical sky sampling, executed by the 8051.
 * Only the original asset conversion takes place on the host. */
#include "graphics.h"
void BankDrawPlane(void)
{
    static uint8_t y,tx,ty,color;
    static int16_t dy,cm;
    static uint16_t skyx,skyy;
    static int32_t ratio,rayx,rayy,distance,plane,worldx,worldy;
    static uint32_t pixels;
    static uint8_t *dest;
    static const uint8_t *shade;
    dest=DdrPointer(DOOM_INDEXED_BASE+(uint16_t)graphics.column*128U);
    if(graphics.flags&DOOM_SKY_FLAG) {
        skyx=(graphics.angle>>22)&(DOOM_SKY_WIDTH-1);
        for(y=graphics.first;y<=graphics.last;++y) {
            skyy=GraphicsDivide((uint16_t)y*128U,DOOM_VIEW_HEIGHT);
            dest[y]=DdrRead(DOOM_SKY_PIXELS+(uint32_t)skyx*128UL+skyy);
        }
        return;
    }
    pixels=((const uint32_t *)DdrPointer(DOOM_FLAT_DIRECTORY))[graphics.pic];
    ratio=FixedDiv(((int16_t)DOOM_VIEW_WIDTH/2-graphics.column)*65536L,(int32_t)(DOOM_VIEW_WIDTH/2)*65536L);
    rayx=graphics.cosine-FixedMul(graphics.sine,ratio);
    rayy=graphics.sine+FixedMul(graphics.cosine,ratio);
    plane=graphics.height-graphics.z;if(plane<0)plane=-plane;
    /* R_ScaleFromGlobalAngle uses a projection of 128 map units, including
     * reduced-height viewports. Keep identical vertical perspective. */
    cm=((256-graphics.light)>>2)-24;if(cm<0)cm=0;if(cm>31)cm=31;
    shade=(const uint8_t *)DdrPointer(0x170010UL)+(uint16_t)cm*256U;
    for(y=graphics.first;y<=graphics.last;++y) {
        dy=(int16_t)y-DOOM_VIEW_HEIGHT/2;if(dy<0)dy=-dy;
        if(!dy){dest[y]=0;continue;}
        distance=FixedDiv(plane,(int32_t)dy*65536L);
        if(distance>0xFFFFFFL)distance=0xFFFFFFL;
        distance*=DOOM_PLANE_PROJECTION;
        worldx=graphics.x+FixedMul(distance,rayx);
        worldy=graphics.y+FixedMul(distance,rayy);
        tx=(worldx>>16)&63;ty=(-worldy>>16)&63;
        color=DdrRead(pixels+(uint16_t)ty*DOOM_FLAT_SIDE+tx);dest[y]=shade[color];
    }
}
