/* Standalone deterministic combat. Not vanilla Doom rules. */
void ProjectileInit(void) __sdcccall(1);
void ProjectileSpawn(uint16_t owner) __sdcccall(1);
typedef struct {
    uint16_t health,ammo,shots,hits,kills,damage,attacks,dead;
    uint8_t wait,flash,hurt,spare;
    uint16_t target;
} combat_state_t;
volatile __xdata __at(0xF700) combat_state_t combat;
volatile __xdata __at(0xF71E) uint8_t combat_hud;
__code __at(0xFF90) const uint16_t combat_schema[] = {sizeof(combat_state_t)};
void R_CombatInit(void)
{
    combat.health=100;combat.ammo=50;
    combat.shots=combat.hits=combat.kills=combat.damage=combat.attacks=combat.dead=0;
    combat.wait=combat.flash=combat.hurt=combat.spare=0;combat.target=0;
    ProjectileInit();
}
uint8_t R_PlayerAlive(void) {return combat.health!=0;}
static void CombatTick(void)
{
    static uint16_t i,best;
    static int16_t x,y,depth,side,nearest,angle;
    static int32_t dx,dy,c,s;
    if(combat.wait)--combat.wait;
    if(combat.flash)--combat.flash;
    if(combat.hurt)--combat.hurt;
    if(!(motion_input.buttons&2) || combat.wait || !combat.ammo || !combat.health)return;
    --combat.ammo;++combat.shots;combat.wait=7;combat.flash=3;combat.target=0;
    x=motion_state.x>>16;y=motion_state.y>>16;angle=motion_state.angle>>19;
    c=finecosineapprox(angle);s=finesineapprox(angle);nearest=1025;best=actor_count;
    for(i=0;i<actor_count;++i) {
        if(!actor_things[i].health)continue;
        dx=((int32_t)actor_things[i].x-x)*65536L;dy=((int32_t)actor_things[i].y-y)*65536L;
        depth=(FixedMul(dx,c)+FixedMul(dy,s))>>16;
        side=(FixedMul(dy,c)-FixedMul(dx,s))>>16;
        if(depth<=0 || depth>=nearest || side< -16 || side>16)continue;
        if(motion_state.floor+41<actor_things[i].floor || motion_state.floor+41>=actor_things[i].floor+56)continue;
        if(!MotionVisible(x,y,actor_things[i].x,actor_things[i].y,motion_state.floor+41))continue;
        nearest=depth;best=i;
    }
    if(best==actor_count)return;
    combat.target=best+1;++combat.hits;actor_things[best].awake=1;actor_things[best].tics=0;
    if(actor_things[best].health<=20) {
        actor_things[best].health=0;actor_things[best].frame=7;++combat.kills;
    } else {actor_things[best].health-=20;actor_things[best].frame=6;}
}
void PlayerDamage(uint8_t damage) __sdcccall(1)
{
    if(!combat.health)return;
    combat.health=combat.health>damage ? combat.health-damage:0;
    combat.damage+=damage;combat.hurt=5;
    if(!combat.health)combat.dead=1;
}
static void CombatAttack(uint16_t id)
{
    static int16_t x,y,z,dx,dy;
    static const uint16_t *kinds;
    ++combat.attacks;
    x=actor_things[id].x;y=actor_things[id].y;z=actor_things[id].floor+32;
    dx=x-(int16_t)(motion_state.x>>16);dy=y-(int16_t)(motion_state.y>>16);
    if(dx< -512 || dx>512 || dy< -512 || dy>512 || !combat.health)return;
    kinds=DdrPointer(0xD3010UL);
    if(dx>=-48 && dx<=48 && dy>=-48 && dy<=48) {
        z=motion_state.floor+41;
        if(z<actor_things[id].floor || z>=actor_things[id].floor+56)return;
        if(MotionVisible(x,y,motion_state.x>>16,motion_state.y>>16,z))PlayerDamage(10);
        return;
    }
    if(kinds[actor_things[id].kind]) {
        if(MotionVisible(x,y,motion_state.x>>16,motion_state.y>>16,z))ProjectileSpawn(id);
    } else {
        z=motion_state.floor+41;
        if(z<actor_things[id].floor || z>=actor_things[id].floor+56)return;
        if(MotionVisible(x,y,motion_state.x>>16,motion_state.y>>16,z))PlayerDamage(10);
    }
}

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
        digit=value/divisor;value%=divisor;divisor/=10;
        bits=hud_digits[digit%10];
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
        sx=(uint16_t)x*patch->width/width;
        address=patch->pixels+(uint32_t)sx*256UL;
        for(y=0;y<height;++y) {
            sy=(uint16_t)y*patch->height/height;
            if(DdrRead(address+(uint16_t)sy*2+1))
                HudPixel((DOOM_VIEW_WIDTH-width)/2+x,bottom-height+y,DdrRead(address+(uint16_t)sy*2));
        }
    }
}
void R_DrawCombatHUD(void)
{
    static uint8_t x,y;
    if(!combat_hud)return;
    if(DOOM_VIEW_HEIGHT>=48) {
        HudPatch(combat.flash ? 1:0,8,DOOM_VIEW_HEIGHT/3,DOOM_VIEW_HEIGHT-9);
        if(combat.flash)HudPatch(2,8,16,DOOM_VIEW_HEIGHT-9-DOOM_VIEW_HEIGHT/3+8);
    }
    HudPixel(DOOM_VIEW_WIDTH/2,DOOM_VIEW_HEIGHT/2,4);
    HudPixel(DOOM_VIEW_WIDTH/2-1,DOOM_VIEW_HEIGHT/2,4);
    HudPixel(DOOM_VIEW_WIDTH/2+1,DOOM_VIEW_HEIGHT/2,4);
    HudNumber(2,combat.health);HudNumber(DOOM_VIEW_WIDTH-13,combat.ammo);
    if(combat.hurt || combat.dead) {
        for(x=0;x<DOOM_VIEW_WIDTH;++x){HudPixel(x,0,176);HudPixel(x,DOOM_VIEW_HEIGHT-1,176);}
        for(y=1;y<DOOM_VIEW_HEIGHT-1;++y){HudPixel(0,y,176);HudPixel(DOOM_VIEW_WIDTH-1,y,176);}
    }
}
