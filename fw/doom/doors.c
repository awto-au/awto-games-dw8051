/* Small native manual-door state machine for the standalone controller.
 * Supports unlocked DR raise/wait/close and D1 raise/stay. Conservative player/actor
 * box obstruction reopens a closing door. No keys, sound or tagged triggers. */
#include "doors.h"
__xdata __at(DOOR_STATE_BASE) door_state_t door_states[DOOR_LIMIT];
volatile __xdata __at(DOOR_INFO_BASE) door_info_t door_info;
static uint32_t defs_base;
static const uint16_t *links;
static __xdata door_def_t definition;
static uint8_t last_use;
static uint8_t (*things_block)(const door_def_t *,int16_t);
void DoorSetThingsBlock(uint8_t (*check)(const door_def_t *,int16_t)) {things_block=check;}
int32_t finesineapprox(int16_t angle);
int32_t finecosineapprox(int16_t angle);

static uint8_t read_def(uint8_t id)
{
    static uint16_t source;
    source=(uint16_t)DdrMapRead(defs_base+((uint16_t)id<<5));
    if(!source)return 0;
    DoomCopy16(((uint32_t)(uint16_t)&definition<<16)|source);
    source=(uint16_t)DdrMapRead(defs_base+((uint16_t)id<<5)+16);
    if(!source)return 0;
    DoomCopy16(((uint32_t)((uint16_t)&definition+16)<<16)|source);
    return 1;
}
void DoorInit(uint32_t data)
{
    static const uint16_t *header;
    static uint8_t i;
    door_info.count=door_info.last_used=door_info.reopens=door_info.fault=0;
    door_info.activations=door_info.updates=0;last_use=0;things_block=0;
    if(!data)return;
    header=DdrPointer(data);
    if(header[0]>DOOR_LIMIT){door_info.fault=1;return;}
    door_info.count=header[0];
    if(!door_info.count)return;
    links=DdrPointer(*(const uint32_t *)(header+2));defs_base=data+16;
    for(i=0;i<door_info.count;++i){
        if(!read_def(i)){door_info.fault=2;return;}
        door_states[i].height=DoorSectorCeiling(definition.sector);
        door_states[i].phase=door_states[i].height<=definition.closed ? DOOR_CLOSED:DOOR_OPEN_STAY;
        door_states[i].wait=door_states[i].stay=door_states[i].reserved=0;
    }
}

static uint8_t occupied(int16_t next)
{
    static int16_t x,y;
    if(things_block && things_block(&definition,next))return 1;
    if(next>=motion_state.floor+MOTION_PLAYER_HEIGHT)return 0;
    x=motion_state.x>>16;y=motion_state.y>>16;
    return x+MOTION_PLAYER_RADIUS>=definition.minx && x-MOTION_PLAYER_RADIUS<=definition.maxx &&
           y+MOTION_PLAYER_RADIUS>=definition.miny && y-MOTION_PLAYER_RADIUS<=definition.maxy;
}
void DoorTick(void)
{
    static uint8_t i,use,token;
    static int16_t angle,end_x,end_y,next;
    static uint16_t j;
    if(!door_info.count || door_info.fault)return;
    use=motion_input.buttons&DOOR_USE_BUTTON;
    if(use && !last_use){
        angle=(uint16_t)(motion_state.angle>>19);
        end_x=(motion_state.x+FixedMul((int32_t)DOOR_USE_RANGE*65536L,finecosineapprox(angle)))>>16;
        end_y=(motion_state.y+FixedMul((int32_t)DOOR_USE_RANGE*65536L,finesineapprox(angle)))>>16;
        token=MotionTraceUse(end_x,end_y);
        i=(token&~DOOR_STAY_TOKEN)-1;
        if(token && i<door_info.count){
            door_info.last_used=i+1;++door_info.activations;
            door_states[i].stay=(token&DOOR_STAY_TOKEN)!=0;
            if(door_states[i].phase!=DOOR_OPENING){door_states[i].phase=DOOR_OPENING;door_states[i].wait=0;}
        }
    }
    last_use=use;
    for(i=0;i<door_info.count;++i){
        if(door_states[i].phase==DOOR_CLOSED || door_states[i].phase==DOOR_OPEN_STAY)continue;
        if(!read_def(i)){door_info.fault=2;return;}
        next=door_states[i].height;
        if(door_states[i].phase==DOOR_WAITING){
            if(door_states[i].wait && !--door_states[i].wait)door_states[i].phase=DOOR_CLOSING;
            continue;
        }
        if(door_states[i].phase==DOOR_OPENING){
            next+=DOOR_SPEED;
            if(next>=definition.top){next=definition.top;door_states[i].phase=door_states[i].stay ? DOOR_OPEN_STAY:DOOR_WAITING;door_states[i].wait=DOOR_WAIT_TICKS;}
        }else{
            next-=DOOR_SPEED;
            if(next<definition.closed)next=definition.closed;
            if(occupied(next)){door_states[i].phase=DOOR_OPENING;++door_info.reopens;continue;}
            if(next==definition.closed)door_states[i].phase=DOOR_CLOSED;
        }
        if(next==door_states[i].height)continue;
        door_states[i].height=next;DoorSetCeiling(definition.sector,next);
        for(j=0;j<definition.count;++j)MotionRefreshLine(links[definition.first+j]);
        MotionWorldChanged();++door_info.updates;
    }
}
