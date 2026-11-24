/* Standalone player/ground-actor collision for the renderer milestone.
 * Bounded 35 Hz commands, outward-rounded player box, live portal heights,
 * axis sliding and floor snapping. No original thinkers, momentum or gravity.
 * All collision decisions execute here as native SDCC MCS51 instructions. */
#include "motion.h"
#include "doors.h"
#include <string.h>

volatile __xdata __at(MOTION_INPUT_BASE) motion_input_t motion_input;
volatile __xdata __at(MOTION_STATE_BASE) motion_state_t motion_state;
static uint32_t line_base;
static const uint16_t *blockmap;
static int16_t origin_x,origin_y;
static uint16_t map_width,map_height,line_count;
static uint8_t fraction;
static int16_t touch_floor,touch_ceiling,centre_floor,centre_ceiling;
static uint8_t query_sector,world_changed,actor_query;
static int16_t query_floor;
static uint8_t (*things_block)(int16_t,int16_t);
void MotionSetThingsBlock(uint8_t (*check)(int16_t,int16_t)) {things_block=check;}
int16_t motion_actor_floor;
static int16_t grid_lx,grid_hx,grid_hy,grid_x,grid_y;
static const uint16_t *grid_list;
static uint16_t grid_remaining;
static __xdata __at(MOTION_VISITED_BASE) uint8_t visited[(MOTION_LINE_LIMIT+7)/8];
static __xdata motion_line_t current;
int32_t finesineapprox(int16_t angle);
int32_t finecosineapprox(int16_t angle);

void MotionInit(uint32_t lines,uint32_t blocks,uint16_t count)
{
    line_base=lines;
    blockmap=DdrPointer(blocks);
    line_count=count;
    origin_x=(int16_t)blockmap[0]; origin_y=(int16_t)blockmap[1];
    map_width=blockmap[2]; map_height=blockmap[3];
    fraction=0;world_changed=0;actor_query=0;things_block=0;
    centre_floor=motion_state.floor;centre_ceiling=motion_state.ceiling;
    motion_state.ticks=0;
    motion_state.blocked=motion_state.frame_ticks=motion_state.fault=motion_state.enabled=0;
    if((int32_t)centre_ceiling-centre_floor<MOTION_PLAYER_HEIGHT)motion_state.fault=4;
    if (!map_width || !map_height || !count || count>MOTION_LINE_LIMIT) motion_state.fault=1;
}

void MotionWorldChanged(void) {world_changed=1;}

void MotionRefreshLine(uint16_t line)
{
    static uint16_t source;
    static uint8_t front,back;
    static int16_t a,b;
    source=(uint16_t)DdrMapRead(line_base+((uint16_t)line<<4));
    if(!source){motion_state.fault=3;return;}
    front=((const __xdata uint8_t *)source)[13];back=((const __xdata uint8_t *)source)[14];
    a=DoorSectorCeiling(front);b=DoorSectorCeiling(back);
    /* Sector reads can evict the profile: reacquire before writing its top. */
    source=(uint16_t)DdrMapWrite(line_base+((uint16_t)line<<4)+10);
    if(!source){motion_state.fault=3;return;}
    *(__xdata int16_t *)source=a<b ? a:b;
}

static void scan_start(int16_t lx,int16_t hx,int16_t ly,int16_t hy)
{
    memset(visited,0,(line_count+7)>>3);
    grid_lx=lx;grid_hx=hx;grid_hy=hy;grid_x=lx-1;grid_y=ly;grid_list=0;
}
static uint16_t scan_next(void)
{
    static uint16_t id;
    static uint8_t mask;
    for(;;){
        if(!grid_list){
            if(++grid_x>grid_hx){grid_x=grid_lx;++grid_y;}
            if(grid_y>grid_hy)return 0xFFFF;
            grid_list=blockmap+blockmap[4+(uint16_t)grid_y*map_width+grid_x]+1;
            grid_remaining=line_count+1;
        }
        if(!grid_remaining--){motion_state.fault=2;return 0xFFFF;}
        id=*grid_list++;
        if(id==0xFFFF){grid_list=0;continue;}
        if(id>=line_count){motion_state.fault=2;return 0xFFFF;}
        mask=(uint8_t)(1u<<(id&7));
        if(visited[id>>3]&mask)continue;
        visited[id>>3]|=mask;
        return id;
    }
}
static uint8_t read_line(uint16_t id)
{
    static uint16_t source;
    source=(uint16_t)DdrMapRead(line_base+((uint16_t)id<<4));
    if(!source){motion_state.fault=3;return 0;}
    DoomCopy16(((uint32_t)(uint16_t)&current<<16)|source);
    return 1;
}

uint8_t MotionTraceUse(int16_t end_x,int16_t end_y)
{
    static int16_t x,y,dx,dy,ex,ey,lx,hx,ly,hy;
    static uint16_t id;
    static int32_t den,t,u,side,fraction,best;
    static uint8_t token;
    x=motion_state.x>>16;y=motion_state.y>>16;dx=end_x-x;dy=end_y-y;
    lx=((int32_t)(x<end_x ? x:end_x)-origin_x)>>7;
    hx=((int32_t)(x>end_x ? x:end_x)-origin_x)>>7;
    ly=((int32_t)(y<end_y ? y:end_y)-origin_y)>>7;
    hy=((int32_t)(y>end_y ? y:end_y)-origin_y)>>7;
    if(lx<0)lx=0;if(ly<0)ly=0;
    if(hx>=map_width)hx=map_width-1;if(hy>=map_height)hy=map_height-1;
    if(lx>hx || ly>hy)return 0;
    scan_start(lx,hx,ly,hy);best=65537L;token=0;
    while((id=scan_next())!=0xFFFF){
        if(!read_line(id))return 0;
        if(!current.use && !(current.flags&MOTION_LINE_SOLID) && current.top>motion_state.floor+MOTION_VIEW_HEIGHT)continue;
        ex=current.x2-current.x1;ey=current.y2-current.y1;
        den=(int32_t)dx*ey-(int32_t)dy*ex;
        if(!den)continue;
        side=((int32_t)x-current.x1)*ey-((int32_t)y-current.y1)*ex;
        t=-side;u=((int32_t)current.x1-x)*dy-((int32_t)current.y1-y)*dx;
        if(den<0){den=-den;t=-t;u=-u;}
        if(t<0 || t>den || u<0 || u>den)continue;
        fraction=FixedDiv(t,den);
        if(fraction<best || (fraction==best && !current.use)){
            best=fraction;token=side>=0 ? current.use:0;
        }
    }
    return token;
}

/* Corner/line cross products fit int32 because asset loading bounds the map
 * span to 16,384 units and coordinates away from int16 limits. Rounded boxes
 * conservatively contain the fixed-point 32x32 player footprint. */
static uint8_t blocked_line(int16_t left,int16_t right,int16_t bottom,int16_t top)
{
    static int16_t dx,dy,ax,ay,bx,by;
    static int32_t lo,hi;
    if(!(current.flags&(MOTION_LINE_SOLID|MOTION_LINE_HEIGHT_CHANGE)))return 0;
    if (right <= (current.x1<current.x2 ? current.x1:current.x2) ||
        left >= (current.x1>current.x2 ? current.x1:current.x2) ||
        top <= (current.y1<current.y2 ? current.y1:current.y2) ||
        bottom >= (current.y1>current.y2 ? current.y1:current.y2)) return 0;
    dx=current.x2-current.x1;dy=current.y2-current.y1;
    ax=dy>=0 ? left:right;bx=dy>=0 ? right:left;
    ay=dx>=0 ? top:bottom;by=dx>=0 ? bottom:top;
    lo=((int32_t)ax-current.x1)*dy-((int32_t)ay-current.y1)*dx;
    hi=((int32_t)bx-current.x1)*dy-((int32_t)by-current.y1)*dx;
    if(lo>0 || hi<0)return 0;
    if ((current.flags & MOTION_LINE_SOLID) ||
        current.bottom > query_floor+MOTION_STEP_HEIGHT ||
        current.top < (current.bottom>query_floor ? current.bottom:query_floor)+MOTION_PLAYER_HEIGHT)return 1;
    query_sector=1;
    if(current.bottom>touch_floor)touch_floor=current.bottom;
    if(current.top<touch_ceiling)touch_ceiling=current.top;
    return 0;
}

static uint8_t try_move(int32_t x,int32_t y)
{
    static int16_t left,right,bottom,top,lx,hx,ly,hy;
    static uint16_t id;
    static int16_t floor,ceiling,next_centre_floor,next_centre_ceiling;
    query_floor=actor_query ? motion_actor_floor:motion_state.floor;
    left=(int16_t)(x>>16)-MOTION_PLAYER_RADIUS;
    right=(int16_t)(x>>16)+MOTION_PLAYER_RADIUS+((uint16_t)x!=0);
    bottom=(int16_t)(y>>16)-MOTION_PLAYER_RADIUS;
    top=(int16_t)(y>>16)+MOTION_PLAYER_RADIUS+((uint16_t)y!=0);
    lx=((int32_t)left-origin_x)>>7;hx=((int32_t)right-origin_x)>>7;
    ly=((int32_t)bottom-origin_y)>>7;hy=((int32_t)top-origin_y)>>7;
    if(lx<0 || ly<0 || hx>=map_width || hy>=map_height) return 0;
    touch_floor=-32768;touch_ceiling=32767;query_sector=0;
    scan_start(lx,hx,ly,hy);
    while((id=scan_next())!=0xFFFF){
        if(!read_line(id))return 0;
        if(blocked_line(left,right,bottom,top))return 0;
    }
    if(motion_state.fault)return 0;
    /* Keep the highest floor / lowest ceiling under the whole player box.
     * A center-only floor snap gets stuck while straddling a downward step. */
    if(query_sector || actor_query)MotionSectorAt(x,y,&floor,&ceiling);
    else {floor=centre_floor;ceiling=centre_ceiling;}
    next_centre_floor=floor;next_centre_ceiling=ceiling;
    if(touch_floor>floor)floor=touch_floor;
    if(touch_ceiling<ceiling)ceiling=touch_ceiling;
    if((int32_t)ceiling-floor<MOTION_PLAYER_HEIGHT || (int32_t)floor-query_floor>MOTION_STEP_HEIGHT)return 0;
    if(actor_query) {
        if((int32_t)query_floor-floor>MOTION_STEP_HEIGHT)return 0;
        motion_actor_floor=floor;return 1;
    }
    if(things_block && things_block(x>>16,y>>16))return 0;
    centre_floor=next_centre_floor;centre_ceiling=next_centre_ceiling;
    motion_state.x=x;motion_state.y=y;
    motion_state.floor=floor;motion_state.ceiling=ceiling;
    return 1;
}

/* A sequential collision query shares map caches, but never overwrites the
 * player's coordinates, floor/ceiling or centre-sector cache. Ground actors
 * currently have the same 16-unit radius and 56-unit height as the player. */
uint8_t MotionActorMove(int16_t x,int16_t y,int16_t floor)
{
    static uint8_t accepted;
    actor_query=1;motion_actor_floor=floor;
    accepted=try_move((int32_t)x*65536L,(int32_t)y*65536L);
    actor_query=0;
    return accepted;
}

/* Horizontal sight segment against live wall/portal profiles. No host LOS. */
uint8_t MotionVisible(int16_t x,int16_t y,int16_t endx,int16_t endy,int16_t eye)
{
    static uint16_t id;
    static int16_t dx,dy,ex,ey;
    static int32_t a,b;
    dx=endx-x;dy=endy-y;
    for(id=0;id<line_count;++id) {
        if(!read_line(id))return 0;
        if(!(current.flags&3))continue;
        if(!(current.flags&1) && eye>=current.bottom && eye<current.top)continue;
        if((x<current.x1 && endx<current.x1 && x<current.x2 && endx<current.x2) ||
           (x>current.x1 && endx>current.x1 && x>current.x2 && endx>current.x2) ||
           (y<current.y1 && endy<current.y1 && y<current.y2 && endy<current.y2) ||
           (y>current.y1 && endy>current.y1 && y>current.y2 && endy>current.y2))continue;
        ex=current.x2-current.x1;ey=current.y2-current.y1;
        a=((int32_t)x-current.x1)*ey-((int32_t)y-current.y1)*ex;
        b=((int32_t)endx-current.x1)*ey-((int32_t)endy-current.y1)*ex;
        if((a>0 && b>0) || (a<0 && b<0))continue;
        a=((int32_t)current.x1-x)*dy-((int32_t)current.y1-y)*dx;
        b=((int32_t)current.x2-x)*dy-((int32_t)current.y2-y)*dx;
        if((a>0 && b>0) || (a<0 && b<0))continue;
        return 0;
    }
    return 1;
}

static void tick(void)
{
    static int16_t f,s,turn,angle;
    static int32_t dx,dy,cosine,sine,x,y;
    f=motion_input.forward;s=motion_input.strafe;turn=motion_input.turn;
    if(f>MOTION_COMMAND_LIMIT)f=MOTION_COMMAND_LIMIT;
    if(f< -MOTION_COMMAND_LIMIT)f= -MOTION_COMMAND_LIMIT;
    if(s>MOTION_COMMAND_LIMIT)s=MOTION_COMMAND_LIMIT;
    if(s< -MOTION_COMMAND_LIMIT)s= -MOTION_COMMAND_LIMIT;
    if(turn>MOTION_TURN_LIMIT)turn=MOTION_TURN_LIMIT;
    if(turn< -MOTION_TURN_LIMIT)turn= -MOTION_TURN_LIMIT;
    motion_state.angle+=(uint32_t)((int32_t)turn*65536L);
    ++motion_state.ticks;
    DoorTick();
    if(exit_info[0])return;
    if(world_changed){
        MotionSectorAt(motion_state.x,motion_state.y,&centre_floor,&centre_ceiling);
        motion_state.ceiling=centre_ceiling;
        world_changed=0;
    }
    if(!f && !s) return;
    angle=(uint16_t)(motion_state.angle>>19);
    cosine=finecosineapprox(angle);sine=finesineapprox(angle);
    dx=FixedMul((int32_t)f*65536L,cosine)-FixedMul((int32_t)s*65536L,sine);
    dy=FixedMul((int32_t)f*65536L,sine)+FixedMul((int32_t)s*65536L,cosine);
    x=motion_state.x;y=motion_state.y;
    if(try_move(x+dx,y+dy))return;
    if(!dx || !dy){motion_state.blocked|=dx ? 1:2;return;}
    if(dx && !try_move(x+dx,y))motion_state.blocked|=1;
    if(dy && !try_move(motion_state.x,y+dy))motion_state.blocked|=2;
}

void MotionFrame(void)
{
    if(exit_info[0]){motion_state.enabled=motion_input.enabled;motion_state.frame_ticks=0;return;}
    if(!motion_input.enabled){motion_state.enabled=0;motion_state.frame_ticks=0;return;}
    motion_state.enabled=1;
    motion_state.blocked=motion_state.frame_ticks=0;
    if(motion_state.fault)return;
    fraction+=MOTION_TICK_HZ;
    while(fraction>=MOTION_FRAME_HZ){
        fraction-=MOTION_FRAME_HZ;
        tick();
        ++motion_state.frame_ticks;
        if(motion_state.fault || exit_info[0])break;
    }
}
