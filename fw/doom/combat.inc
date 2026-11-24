/* Standalone deterministic combat. Not vanilla Doom rules. */
#define HUD_KEY_BLUE_INDEX 200
#define HUD_KEY_YELLOW_INDEX 160
#define HUD_KEY_RED_INDEX 176
void ProjectileInit(void) __sdcccall(1);
void ProjectileSpawn(uint16_t owner) __sdcccall(1);
void PickupInit(void) __sdcccall(1);
volatile __xdata __at(0xF740) uint16_t pickup_info[4];
volatile __xdata __at(0xF700) combat_state_t combat;
volatile __xdata __at(0xF71E) uint8_t combat_hud;
__code __at(0xFF90) const uint16_t combat_schema[] = {sizeof(combat_state_t)};
void R_CombatInit(void)
{
    combat.health=100;combat.ammo=50;
    combat.shots=combat.hits=combat.kills=combat.damage=combat.attacks=combat.dead=0;
    combat.wait=combat.flash=combat.hurt=combat.spare=0;combat.target=0;
    ProjectileInit();
    PickupInit();
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
    if(kinds[actor_things[id].kind]==2)return;
    if(kinds[actor_things[id].kind]) {
        if(MotionVisible(x,y,motion_state.x>>16,motion_state.y>>16,z))ProjectileSpawn(id);
    } else {
        z=motion_state.floor+41;
        if(z<actor_things[id].floor || z>=actor_things[id].floor+56)return;
        if(MotionVisible(x,y,motion_state.x>>16,motion_state.y>>16,z))PlayerDamage(10);
    }
}
