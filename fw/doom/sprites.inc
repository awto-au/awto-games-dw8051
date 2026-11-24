/* Standalone ground actors. Native movement, animation, projection and clips.
 * WAD conversion is offline. Standalone combat is separate from the original Doom thinker system. */
#include "motion.h"
#include "actor_types.h"
__code __at(0xFF80) const uint16_t sprite_schema[] = {sizeof(static_thing_t),sizeof(static_patch_t),2};
volatile __xdata __at(0xF6D0) uint16_t sprite_info[4];
static void R_StaticSprites(void)
{
    static static_thing_t *things,*thing;
    static const static_patch_t *patches,*patch;
    static const uint16_t *header;
    static const uint8_t *shade;
    static const drawseg_t *ds;
    static sector_t *sector;
    static uint8_t *dest;
    static uint16_t count,monsters,i,best,rot;
    static int16_t x,x1,x2,y,y1,y2,sx,sy,cliptop,clipbot,floor,light;
    static int32_t dx,dy,tx,tz,scale,xscale,left,top,stepx,stepy,u,v,maxdepth;
    static uint32_t address;
    static uint8_t color;
    header=DdrPointer(0xD0010UL);things=DdrPointer(0xD0020UL);patches=DdrPointer(0xE0010UL);
    monsters=header[0];count=header[1];
    if(count>136+DOOM_PICKUP_MAX) {ddr_fault=5;return;}
    sprite_info[0]=count;sprite_info[1]=0;sprite_info[2]=0;sprite_info[3]=0;
    for(i=0;i<count;++i) {
        thing=things+i;
        if(i>=monsters && !thing->health){thing->depth=0;continue;}
        dx=(int32_t)thing->x*65536L-viewx;dy=(int32_t)thing->y*65536L-viewy;
        tz=FixedMul(dx,viewcos)+FixedMul(dy,viewsin);
        tx=FixedMul(dx,viewsin)-FixedMul(dy,viewcos);
        if(tz<4L*65536L || tz>1280L*65536L || tx>tz*2 || tx< -tz*2) tz=0;
        else ++sprite_info[1];
        thing->depth=tz;
    }
    /* Back to front selection in DDR keeps MCU SRAM bounded. */
    for(;;) {
        maxdepth=0;best=count;
        for(i=0;i<count;++i) {
            tz=things[i].depth;
            if(tz>maxdepth) {maxdepth=tz;best=i;}
        }
        if(best==count) break;
        thing=things+best;thing->depth=0;tz=maxdepth;
        dx=(int32_t)thing->x*65536L;dy=(int32_t)thing->y*65536L;
        rot=(uint16_t)(R_PointToAngle16(thing->x,thing->y)-thing->angle+0x9000U)>>13;
        patch=patches+thing->kind*96+(uint16_t)thing->frame*8+rot;
        if(!patch->width) continue;
        sector=R_PointInSubsector(dx,dy)->sector;
        floor=sector->floorheight>>16;light=sector->lightlevel;
        if(best>=monsters && best<monsters+8){floor=thing->floor;light=255;}
        tx=FixedMul(dx-viewx,viewsin)-FixedMul(dy-viewy,viewcos);
        xscale=PROJECTION/(tz>>16);scale=((int32_t)DOOM_VIEW_HEIGHT*65536L)/(tz>>16);
        tx-=(int32_t)(patch->flip ? patch->width-patch->left : patch->left)*65536L;
        left=(int32_t)CENTERX*65536L+FixedMul(tx,xscale);
        x1=left>>16;
        x2=((int32_t)CENTERX*65536L+FixedMul(tx+(int32_t)patch->width*65536L,xscale)-1)>>16;
        if(x1>=VIEWWINDOWWIDTH || x2<0 || x2<x1) continue;
        if(x1<0)x1=0;if(x2>=VIEWWINDOWWIDTH)x2=VIEWWINDOWWIDTH-1;
        top=(int32_t)CENTERY*65536L-FixedMul(((int32_t)floor+patch->top)*65536L-viewz,scale);
        y1=top>>16;y2=(top+FixedMul((int32_t)patch->height*65536L,scale)-1)>>16;
        if(y1>=DOOM_VIEW_HEIGHT || y2<0)continue;
        if(y1<0)y1=0;if(y2>=DOOM_VIEW_HEIGHT)y2=DOOM_VIEW_HEIGHT-1;
        stepx=FixedDiv(65536L,xscale);stepy=FixedDiv(65536L,scale);
        curline=0;shade=R_LoadColorMap(light);
        ++sprite_info[2];
        u=FixedMul((int32_t)x1*65536L-left,stepx);
        for(x=x1;x<=x2;++x,u+=stepx) {
            cliptop=-1;clipbot=DOOM_VIEW_HEIGHT;
            for(ds=_s_drawsegs;ds<ds_p;++ds) {
                if(x<ds->x1 || x>ds->x2 || !ds->silhouette) continue;
                if(ds->scale1+(int32_t)(x-ds->x1)*ds->scalestep<scale)continue;
                if((ds->silhouette&2) && ((int32_t)floor+patch->top)*65536L>ds->tsilheight) {
                    if(ds->sprtopclip[x]>cliptop)cliptop=ds->sprtopclip[x];
                }
                if((ds->silhouette&1) && (int32_t)floor*65536L<ds->bsilheight) {
                    if(ds->sprbottomclip[x]<clipbot)clipbot=ds->sprbottomclip[x];
                }
            }
            sx=u>>16;
            if(sx<0 || sx>=patch->width)continue;
            if(patch->flip)sx=patch->width-1-sx;
            address=patch->pixels+(uint32_t)sx*256UL;
            dest=DdrPointer(DOOM_INDEXED_BASE+(uint16_t)x*128U);
            v=FixedMul((int32_t)y1*65536L-top,stepy);
            for(y=y1;y<=y2;++y,v+=stepy) {
                if(y<=cliptop || y>=clipbot)continue;
                sy=v>>16;
                if(sy<0 || sy>=patch->height)continue;
                if(!DdrRead(address+(uint16_t)sy*2U+1))continue;
                color=DdrRead(address+(uint16_t)sy*2U);dest[y]=shade[color];++sprite_info[3];
            }
        }
    }
}
