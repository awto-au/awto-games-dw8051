/* Eight bounded native fireballs. Fixed trajectory; no host steering/rendering. */
#include "actor_types.h"
#include "motion.h"
extern static_thing_t *actor_things;
extern uint16_t actor_count;
void PlayerDamage(uint8_t damage) __sdcccall(1);
typedef struct {int32_t x,y;int16_t vx,vy;uint16_t age,owner;} projectile_t;
volatile __xdata __at(0xF720) uint16_t projectile_info[8];
__code __at(0xFF94) const uint16_t projectile_schema[]={sizeof(projectile_t),8};
static projectile_t *projectile_states;
static static_thing_t *projectile_sprites;
void ProjectileInit(void) __sdcccall(1)
{
    static uint8_t i;
    static uint16_t *header;
    header=DdrPointer(0xD0010UL);header[1]=actor_count+8;
    projectile_states=DdrPointer(0xD6010UL);
    projectile_sprites=actor_things+actor_count;
    for(i=0;i<8;++i){projectile_info[i]=0;projectile_sprites[i].health=0;}
}
void ProjectileSpawn(uint16_t owner) __sdcccall(1)
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
void ProjectileTick(void) __sdcccall(1)
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
