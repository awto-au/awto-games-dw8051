/* Standalone sight/chase/combat states. Decisions execute on the 8051.
 * The same fixed 35/25 tick budget as the player drives this prototype. */
#include "doors.h"
static void CombatTick(void);
static void CombatAttack(uint16_t id);
void ProjectileTick(void) __sdcccall(1);
volatile __xdata __at(0xF6E0) uint16_t actor_info[4];
static_thing_t *actor_things;
uint16_t actor_count;

static uint8_t ActorPlayerBlocked(int16_t x,int16_t y)
{
    static uint16_t j;
    static int16_t dx,dy;
    for(j=0;j<actor_count;++j) {
        if(!actor_things[j].health)continue;
        dx=x-actor_things[j].x;dy=y-actor_things[j].y;
        /* Outward-round fixed player coordinates by one map unit. */
        if(dx> -33 && dx<33 && dy> -33 && dy<33)return 1;
    }
    return 0;
}
static uint8_t ActorDoorBlocked(const door_def_t *door,int16_t next)
{
    static uint16_t j;
    static int16_t x,y;
    for(j=0;j<actor_count;++j) {
        if(!actor_things[j].health)continue;
        if(next>=actor_things[j].floor+56)continue;
        x=actor_things[j].x;y=actor_things[j].y;
        if(x+16>=door->minx && x-16<=door->maxx && y+16>=door->miny && y-16<=door->maxy)return 1;
    }
    return 0;
}
void R_ActorInit(void)
{
    static const uint16_t *header;
    static uint16_t j;
    static int16_t ceiling;
    header=DdrPointer(0xD0010UL);actor_count=header[0];actor_things=DdrPointer(0xD0020UL);
    if(actor_count>128){ddr_fault=5;actor_count=0;return;}
    for(j=0;j<actor_count;++j) {
        if(!actor_things[j].health)actor_things[j].health=20;
        MotionSectorAt((int32_t)actor_things[j].x*65536L,(int32_t)actor_things[j].y*65536L,&actor_things[j].floor,&ceiling);
    }
    MotionSetThingsBlock(ActorPlayerBlocked);
    DoorSetThingsBlock(ActorDoorBlocked);
}

static uint8_t ActorFits(static_thing_t *things,uint16_t count,uint16_t id,int16_t x,int16_t y)
{
    static uint16_t j;
    static int16_t dx,dy;
    dx=x-(int16_t)(motion_state.x>>16);dy=y-(int16_t)(motion_state.y>>16);
    if(dx> -33 && dx<33 && dy> -33 && dy<33)return 0;
    for(j=0;j<count;++j) {
        if(j==id || !things[j].health)continue;
        dx=x-things[j].x;dy=y-things[j].y;
        if(dx> -32 && dx<32 && dy> -32 && dy<32)return 0;
    }
    return MotionActorMove(x,y,things[id].floor);
}

void R_ActorFrame(void)
{
    static static_thing_t *things,*thing;
    static const uint16_t *header;
    static uint16_t count,i;
    static uint8_t tick,moved;
    static int16_t x,y,px,py,dx,dy,sx,sy,ceiling;
    if(!motion_state.enabled || !motion_state.frame_ticks)return;
    header=DdrPointer(0xD0010UL);things=DdrPointer(0xD0020UL);count=header[0];
    if(count>128){ddr_fault=5;return;}
    px=motion_state.x>>16;py=motion_state.y>>16;
    for(tick=0;tick<motion_state.frame_ticks;++tick) {
        CombatTick();
        ProjectileTick();
        ++actor_info[0];actor_info[3]=0;
        for(i=0;i<count;++i) {
            thing=things+i;x=thing->x;y=thing->y;
            dx=px-x;dy=py-y;
            if(!thing->health) {
                if(thing->frame<11 && ++thing->tics>=4){++thing->frame;thing->tics=0;}
                continue;
            }
            if(thing->frame>=4) {
                if(thing->awake)++actor_info[3];
                ++thing->tics;
                if(thing->frame==4 && thing->tics>=8){CombatAttack(i);thing->frame=5;thing->tics=0;}
                else if((thing->frame==5 && thing->tics>=27) || (thing->frame==6 && thing->tics>=6)){thing->frame=0;thing->tics=0;}
                continue;
            }
            if(!thing->awake) {
                if(dx< -512 || dx>512 || dy< -512 || dy>512)continue;
                if(!MotionVisible(px,py,x,y,motion_state.floor+41))continue;
                MotionSectorAt((int32_t)x*65536L,(int32_t)y*65536L,&thing->floor,&ceiling);
                thing->awake=1;
            }
            ++actor_info[3];++thing->tics;
            thing->frame=(thing->tics>>3)&3;
            if(!(thing->tics&31) && dx>=-512 && dx<=512 && dy>=-512 && dy<=512 &&
               MotionVisible(x,y,px,py,motion_state.floor+41)) {
                thing->frame=4;thing->tics=0;continue;
            }
            if(thing->tics&3)continue;
            /* Keep the whole-body floor from the last successful probe.
             * A centre-only snap while stopped on stairs can sink the body. */
            /* Choose one of eight directions, slide along walls if needed. */
            sx=dx>4 ? 4:(dx< -4 ? -4:0);sy=dy>4 ? 4:(dy< -4 ? -4:0);
            if(sx && sy){sx=sx>0 ? 3:-3;sy=sy>0 ? 3:-3;}
            if(!sx && !sy)continue;
            if(sy>0)thing->angle=sx>0 ? 0x2000:(sx<0 ? 0x6000:0x4000);
            else if(sy<0)thing->angle=sx>0 ? 0xE000:(sx<0 ? 0xA000:0xC000);
            else thing->angle=sx>0 ? 0:0x8000;
            moved=ActorFits(things,count,i,x+sx,y+sy);
            if(moved){x+=sx;y+=sy;}
            else if(sx && sy) {
                moved=ActorFits(things,count,i,x+sx,y);
                if(moved)x+=sx;
                else {moved=ActorFits(things,count,i,x,y+sy);if(moved)y+=sy;}
            }
            if(moved){thing->x=x;thing->y=y;thing->floor=motion_actor_floor;++actor_info[1];}
            else ++actor_info[2];
        }
    }
}
