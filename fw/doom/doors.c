/* Small native manual-door state machine for the standalone controller.
 * Manual raise/wait/close and raise/stay, with per-line colour locks.
 * Conservative player/actor obstruction reopens a closing door. */
#include "doors.h"
__xdata __at(DOOR_STATE_BASE) door_state_t door_states[DOOR_LIMIT];
volatile __xdata __at(DOOR_INFO_BASE) door_info_t door_info;
volatile __xdata __at(KEY_INFO_BASE) uint16_t key_info[4];
volatile __xdata __at(SWITCH_INFO_BASE) uint16_t switch_info[4];
__xdata __at(SWITCH_TIMER_BASE) uint8_t switch_timers[SWITCH_LIMIT];
volatile __xdata __at(EXIT_INFO_BASE) uint16_t exit_info[4];
static uint32_t switch_base,action_base;
static uint8_t switch_count;
static __xdata switch_def_t button_definition;
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
static uint8_t read_switch(uint8_t id)
{
    uint16_t source=(uint16_t)DdrMapRead(switch_base+16+((uint16_t)id<<4));
    if(!source){door_info.fault=3;return 0;}
    DoomCopy16(((uint32_t)(uint16_t)&button_definition<<16)|source);
    return 1;
}
static void switch_texture(uint8_t on)
{
    int16_t *p;
    if(!button_definition.texture)return;
    p=DdrPointer(button_definition.texture);*p=on ? button_definition.on:button_definition.off;
}
void DoorInit(uint32_t data)
{
    static const uint16_t *header;
    static uint8_t i;
    door_info.count=door_info.last_used=door_info.reopens=door_info.fault=0;
    door_info.activations=door_info.updates=0;last_use=0;things_block=0;
    for(i=0;i<4;++i)key_info[i]=0;
    switch_base=action_base=0;switch_count=0;
    for(i=0;i<4;++i)switch_info[i]=0;
    for(i=0;i<4;++i)exit_info[i]=0;
    exit_info[1]=65535;
    for(i=0;i<SWITCH_LIMIT;++i)switch_timers[i]=0;
    if(!data)return;
    header=DdrPointer(data);
    if(header[0]>DOOR_LIMIT){door_info.fault=1;return;}
    door_info.count=header[0];
    action_base=*(const uint32_t *)(header+6);
    switch_base=*(const uint32_t *)(header+4);
    if(switch_base) {
        header=DdrPointer(switch_base);
        if(header[0]>SWITCH_LIMIT){door_info.fault=3;return;}
        switch_count=header[0];
        header=DdrPointer(data);
    }
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
    static uint8_t i,use,token,colour,required,button;
    static int16_t angle,end_x,end_y,next;
    static uint16_t j,action;
    static uint32_t targets;
    if(key_info[3] && !--key_info[3])key_info[1]=0;
    if(exit_info[0] || (!door_info.count && !switch_count) || door_info.fault)return;
    for(button=0;button<switch_count;++button) {
        if(switch_timers[button] && !--switch_timers[button]) {
            if(!read_switch(button))return;
            switch_texture(0);++switch_info[1];
        }
    }
    use=motion_input.buttons&DOOR_USE_BUTTON;
    if(use && !last_use){
        angle=(uint16_t)(motion_state.angle>>19);
        end_x=(motion_state.x+FixedMul((int32_t)DOOR_USE_RANGE*65536L,finecosineapprox(angle)))>>16;
        end_y=(motion_state.y+FixedMul((int32_t)DOOR_USE_RANGE*65536L,finesineapprox(angle)))>>16;
        token=MotionTraceUse(end_x,end_y);
        action=token ? ((const uint16_t *)DdrPointer(action_base))[token]:0;
        i=(action&DOOR_ACTION_ID_MASK)-1;
        if(action&DOOR_ACTION_SWITCH) {
            button=i;
            if(button<switch_count && !(switch_info[2]&(1U<<button)) && !switch_timers[button]) {
                if(!read_switch(button))return;
                targets=button_definition.targets;
                if(targets || button_definition.kind) {
                    switch_texture(1);++switch_info[0];switch_info[3]=button+1;
                    if(action&DOOR_ACTION_REPEAT)switch_timers[button]=SWITCH_RESET_TICKS;
                    else switch_info[2]|=1U<<button;
                    if(button_definition.kind) {
                        exit_info[0]=button_definition.kind;exit_info[1]=button_definition.line;++exit_info[2];
                        return;
                    }
                    for(i=0;i<door_info.count;++i)if(targets&(1UL<<i)) {
                        door_info.last_used=i+1;++door_info.activations;
                        door_states[i].stay=(action&DOOR_ACTION_STAY)!=0;
                        door_states[i].phase=DOOR_OPENING;door_states[i].wait=0;
                    }
                }
            }
        } else if(token && i<door_info.count){
            colour=(action>>DOOR_ACTION_KEY_SHIFT)&3;
            required=colour==1 ? KEY_BLUE_MASK:(colour==2 ? KEY_YELLOW_MASK:KEY_RED_MASK);
            if(colour && !(key_info[0]&required)) {
                key_info[1]=1U<<(colour-1);++key_info[2];key_info[3]=KEY_NOTICE_TICKS;
            } else {
                key_info[1]=key_info[3]=0;
                door_info.last_used=i+1;++door_info.activations;
                door_states[i].stay=(action&DOOR_ACTION_STAY)!=0;
                if(door_states[i].phase!=DOOR_OPENING){door_states[i].phase=DOOR_OPENING;door_states[i].wait=0;}
            }
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
