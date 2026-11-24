/* Native graphics-bank HUD. No host pixels or gameplay decisions. */
#include "actor_types.h"
#include "graphics.h"
#include "doors.h"
#define HUD_KEY_BLUE_INDEX 200
#define HUD_KEY_YELLOW_INDEX 160
#define HUD_KEY_RED_INDEX 176
extern volatile __xdata __at(0xF700) combat_state_t combat;
extern volatile __xdata __at(0xF740) uint16_t pickup_info[4];
extern volatile __xdata __at(0xF71E) uint8_t combat_hud;
static void HudPixel(uint8_t x,uint8_t y,uint8_t color)
{
    uint8_t *p=DdrPointer(DOOM_INDEXED_BASE+(uint16_t)x*128U+y);*p=color;
}
static const __code uint16_t hud_digits[10]={0x7B6F,0x2492,0x73E7,0x73CF,0x5BC9,0x79CF,0x79EF,0x7249,0x7BEF,0x7BCF};
static void HudNumber(uint8_t x,uint16_t value)
{
    static uint8_t digit,row,col,n;
    static uint16_t bits,divisor;
    divisor=100;
    for(n=0;n<3;++n) {
        digit=GraphicsDivide(value,divisor);value-=(uint16_t)digit*divisor;divisor=n==0 ? 10:1;
        bits=hud_digits[digit];
        for(row=0;row<5;++row)for(col=0;col<3;++col)
            HudPixel(x+col,DOOM_VIEW_HEIGHT-7+row,(bits&(1U<<(14-row*3-col))) ? 4:0);
        x+=4;
    }
}
static void HudPatch(uint8_t id,uint8_t width,uint8_t height,uint8_t bottom)
{
    static const static_patch_t *patch;
    static uint8_t x,y,sx,sy;
    static uint32_t address;
    patch=(const static_patch_t *)DdrPointer(0x1D0010UL)+id;
    for(x=0;x<width;++x) {
        sx=GraphicsDivide((uint16_t)x*patch->width,width);
        address=patch->pixels+(uint32_t)sx*256UL;
        for(y=0;y<height;++y) {
            sy=GraphicsDivide((uint16_t)y*patch->height,height);
            if(DdrRead(address+(uint16_t)sy*2+1))
                HudPixel((((uint8_t)(DOOM_VIEW_WIDTH-width))>>1)+x,bottom-height+y,DdrRead(address+(uint16_t)sy*2));
        }
    }
}
static const __code uint16_t hud_exit_glyphs[4]={0x79a7,0x5aad,0x7497,0x7492};
void R_DrawCombatHUD(void)
{
    static uint8_t x,y,k,owned,needed,color;
    if(!combat_hud)return;
    if(DOOM_VIEW_HEIGHT>=48) {
        HudPatch(combat.flash ? 1:0,8,DOOM_VIEW_HEIGHT/3,DOOM_VIEW_HEIGHT-9);
        if(combat.flash)HudPatch(2,8,16,DOOM_VIEW_HEIGHT-9-DOOM_VIEW_HEIGHT/3+8);
    }
    HudPixel(DOOM_VIEW_WIDTH/2,DOOM_VIEW_HEIGHT/2,4);
    HudPixel(DOOM_VIEW_WIDTH/2-1,DOOM_VIEW_HEIGHT/2,4);
    HudPixel(DOOM_VIEW_WIDTH/2+1,DOOM_VIEW_HEIGHT/2,4);
    HudNumber(2,combat.health);HudNumber(DOOM_VIEW_WIDTH-13,combat.ammo);
    for(k=0;k<3;++k) {
        owned=(key_info[0]&(KEY_BLUE_MASK<<k))!=0;
        needed=(key_info[1]&(1U<<k)) && key_info[3];
        if(!owned && !(needed && (key_info[3]&4)))continue;
        color=k==0 ? HUD_KEY_BLUE_INDEX:(k==1 ? HUD_KEY_YELLOW_INDEX:HUD_KEY_RED_INDEX);
        for(x=0;x<3;++x)for(y=0;y<3;++y)HudPixel(2+k*5+x,2+y,color);
    }
    if(exit_info[0]) {
        for(x=DOOM_VIEW_WIDTH/2-10;x<DOOM_VIEW_WIDTH/2+10;++x)
            for(y=6;y<15;++y)HudPixel(x,y,0);
        for(k=0;k<4;++k)for(y=0;y<5;++y)for(x=0;x<3;++x)
            HudPixel(DOOM_VIEW_WIDTH/2-7+k*4+x,8+y,(hud_exit_glyphs[k]&(1U<<(14-y*3-x))) ? 4:0);
    }
    if(combat.hurt || combat.dead || pickup_info[3]) {
        uint8_t color=(combat.hurt || combat.dead) ? 176:160;
        for(x=0;x<DOOM_VIEW_WIDTH;++x){HudPixel(x,0,color);HudPixel(x,DOOM_VIEW_HEIGHT-1,color);}
        for(y=1;y<DOOM_VIEW_HEIGHT-1;++y){HudPixel(0,y,color);HudPixel(DOOM_VIEW_WIDTH-1,y,color);}
    }
}
