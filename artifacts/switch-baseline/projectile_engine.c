/* Eight bounded native fireballs. Fixed trajectory; no host steering/rendering. */
#include "actor_types.h"
#include "motion.h"
#include "doors.h"
extern static_thing_t *actor_things;
extern uint16_t actor_count;
void PlayerDamage(uint8_t damage) __sdcccall(1);
typedef struct {int32_t x,y;int16_t vx,vy;uint16_t age,owner;} projectile_t;
volatile __xdata __at(0xF720) uint16_t projectile_info[8];

static projectile_t *projectile_states;
static static_thing_t *projectile_sprites;
void BankProjectileInit(void) __sdcccall(1)
{
    static uint8_t i;
    static uint16_t *header;
    header=DdrPointer(0xD0010UL);header[1]=actor_count+8;
    projectile_states=DdrPointer(0xD6010UL);
    projectile_sprites=actor_things+actor_count;
    for(i=0;i<8;++i){projectile_info[i]=0;projectile_sprites[i].health=0;}
}
void BankProjectileSpawn(uint16_t owner) __sdcccall(1)
{
    static uint8_t i;
    static int16_t dx,dy,den;
    static projectile_t *p;
    static static_thing_t *v;
    static const uint16_t *header;
    for(i=0;i<8;++i)if(!projectile_sprites[i].health)break;
    if(i==8){++projectile_info[6];return;}
    p=projectile_states+i;v=projectile_sprites+i;
    v->x=actor_things[owner].x;v->y=actor_things[owner].y;
    v->floor=actor_things[owner].floor+32;
    p->x=(int32_t)v->x*65536L;p->y=(int32_t)v->y*65536L;
    dx=(motion_state.x>>16)-v->x;dy=(motion_state.y>>16)-v->y;
    den=dx<0 ? -dx:dx;if((dy<0 ? -dy:dy)>den)den=dy<0 ? -dy:dy;
    if(!den)return;
    p->vx=FixedDiv(dx,den)>>5;p->vy=FixedDiv(dy,den)>>5;
    p->age=0;p->owner=owner;
    header=DdrPointer(0xD0010UL);v->kind=header[2];
    v->angle=v->tics=0;v->frame=0;v->awake=1;v->health=1;
    ++projectile_info[0];
}
void BankProjectileTick(void) __sdcccall(1)
{
    static uint8_t i,step;
    static int16_t x,y,nx,ny,dx,dy;
    static projectile_t *p;
    static static_thing_t *v;
    projectile_info[7]=0;
    for(i=0;i<8;++i) {
        v=projectile_sprites+i;if(!v->health)continue;
        ++projectile_info[7];p=projectile_states+i;
        if(v->awake==2) {
            if(++v->tics>=4){v->tics=0;if(++v->frame>4)v->health=0;}
            continue;
        }
        if(++p->age>105){v->health=0;++projectile_info[5];continue;}
        v->frame=(p->age>>2)&1;
        for(step=0;step<4;++step) {
            x=p->x>>16;y=p->y>>16;
            p->x+=(int32_t)p->vx*64L;p->y+=(int32_t)p->vy*64L;
            nx=p->x>>16;ny=p->y>>16;
            if(!MotionVisible(x,y,nx,ny,v->floor)) {
                v->awake=2;v->frame=2;v->tics=0;++projectile_info[2];break;
            }
            v->x=nx;v->y=ny;++projectile_info[1];
            dx=nx-(int16_t)(motion_state.x>>16);dy=ny-(int16_t)(motion_state.y>>16);
            if(dx>=-20 && dx<=20 && dy>=-20 && dy<=20 && v->floor>=motion_state.floor && v->floor<motion_state.floor+56) {
                PlayerDamage(10);v->awake=2;v->frame=2;v->tics=0;++projectile_info[3];break;
            }
        }
    }
}

/* Map pickups share the native sprite pass but never block actors or doors. */
extern volatile __xdata __at(0xF700) combat_state_t combat;
extern volatile __xdata __at(0xF740) uint16_t pickup_info[4];
static static_thing_t *pickup_things;
static uint16_t pickup_count;
void BankPickupInit(void) __sdcccall(1)
{
    static uint16_t i,*header;
    static int16_t ceiling;
    header=DdrPointer(DOOM_PICKUP_HEADER_BASE);pickup_count=header[0];
    if(pickup_count>DOOM_PICKUP_MAX){ddr_fault=6;pickup_count=0;return;}
    pickup_things=actor_things+actor_count+8;
    header=DdrPointer(0xD0010UL);header[1]=actor_count+8+pickup_count;
    for(i=0;i<4;++i)pickup_info[i]=0;
    for(i=0;i<pickup_count;++i) {
        if(pickup_things[i].tics>=DOOM_PICKUP_RULES){ddr_fault=6;return;}
        MotionSectorAt((int32_t)pickup_things[i].x*65536L,(int32_t)pickup_things[i].y*65536L,&pickup_things[i].floor,&ceiling);
    }
}
void BankPickupTick(void) __sdcccall(1)
{
    static uint16_t i,amount,value,cap;
    static int16_t x,y,dx,dy,dz;
    static static_thing_t *p;
    if(!combat.health)return;
    if(pickup_info[3])--pickup_info[3];
    x=motion_state.x>>16;y=motion_state.y>>16;
    for(i=0;i<pickup_count;++i) {
        p=pickup_things+i;if(!p->health)continue;
        dx=p->x-x;dy=p->y-y;dz=p->floor-motion_state.floor;
        if(dx< -DOOM_PICKUP_RADIUS || dx>DOOM_PICKUP_RADIUS || dy< -DOOM_PICKUP_RADIUS || dy>DOOM_PICKUP_RADIUS || dz< -8 || dz>56)continue;
        if(!MotionVisible(x,y,p->x,p->y,p->floor+4))continue;
        if(p->tics>=DOOM_FIRST_KEY_RULE) {
            amount=1U<<(p->tics-DOOM_FIRST_KEY_RULE);
            if(key_info[0]&amount)continue;
            key_info[0]|=amount;
        } else {
        if(p->tics<3) {
            value=combat.health;cap=p->tics==2 ? DOOM_BONUS_HEALTH:DOOM_NORMAL_HEALTH;
            amount=p->tics==0 ? 10:(p->tics==1 ? 25:1);
        } else {value=combat.ammo;cap=DOOM_MAX_BULLETS;amount=p->tics==3 ? 10:50;}
        if(value>=cap)continue;
        if(amount>cap-value)amount=cap-value;
        if(p->tics<3){combat.health+=amount;pickup_info[1]+=amount;}
        else {combat.ammo+=amount;pickup_info[2]+=amount;}
        }
        p->health=0;++pickup_info[0];pickup_info[3]=DOOM_PICKUP_FLASH_TICKS;
    }
}
