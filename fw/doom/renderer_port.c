/* First native Doom8088 renderer integration: walls, BSP and flat planes.
 * Assets are preloaded into DDR. Native movement/collision, manual doors and animated ground actors; no original game thinkers.
 * Engine code and licences: vendor/Doom8088, commit b3073a2e. */
#include "platform.h"
#include "motion.h"
#include "doors.h"
#include "globdata.h"
#include <stddef.h>
__sfr __at(DOOM_SFR_CKCON) doom_ckcon;

const seg_t *_g_segs;
int16_t _g_numsectors, _g_numlines;
sector_t *_g_sectors;
subsector_t *_g_subsectors;
line_t *_g_lines;
side_t *_g_sides;
uint16_t _g_gamma;
int32_t _g_gametic = 1;
player_t _g_player;
int16_t skyflatnum = -2;
static mobj_t camera;
static uint8_t *screen, *palette;
static const texture_t *textures;
static const uint32_t *texture_pixels;
static __xdata __at(DOOM_CACHE_PALETTE_BASE) uint8_t palette_xram[DOOM_PALETTE_BYTES];
__xdata uint16_t doom_column_target, doom_column_frac, doom_column_step;
__xdata uint8_t doom_column_count;

typedef struct {
    uint32_t segs, sectors, subsectors, lines, sides, nodes;
    uint32_t textureinfo, texturepixels, heights, translations, palette;
    int16_t nodecount, sectorcount, linecount;
    int32_t x, y;
    uint32_t angle;
    int32_t viewz;
    uint32_t collisionlines,blockmap,doors;
} boot_t;
volatile __xdata __at(0xF640) boot_t renderer_boot;
volatile __xdata __at(0xF600) uint8_t renderer_status[16];
volatile __xdata __at(0xF630) uint8_t renderer_frames;
volatile __xdata __at(0xF631) uint8_t renderer_ack;
volatile __xdata __at(0xF632) uint8_t renderer_frames_hi;
volatile __xdata __at(0xF634) uint32_t renderer_angle_step;

/* Read by the asset packer from the linked image, so host C layout and pointer
 * width cannot silently differ from SDCC. Values are little-endian uint16_t. */
#define O(T,F) offsetof(T,F)
__code __at(0xFF00) const uint16_t renderer_schema[] = {
    sizeof(sector_t), O(sector_t,floorheight), O(sector_t,ceilingheight),
    O(sector_t,floorpic), O(sector_t,ceilingpic), O(sector_t,lightlevel),
    sizeof(side_t), O(side_t,sector), O(side_t,textureoffset), O(side_t,rowoffset),
    O(side_t,toptexture), O(side_t,bottomtexture), O(side_t,midtexture),
    sizeof(line_t), O(line_t,v1), O(line_t,v2), O(line_t,dx), O(line_t,dy),
    O(line_t,sidenum), O(line_t,bbox), O(line_t,flags), O(line_t,r_validcount),
    sizeof(subsector_t), O(subsector_t,sector), O(subsector_t,numlines), O(subsector_t,firstline),
    sizeof(texture_t), O(texture_t,widthmask), O(texture_t,width), O(texture_t,height),
    sizeof(seg_t), sizeof(mapnode_t), sizeof(boot_t),
    sizeof(motion_line_t), sizeof(motion_input_t), sizeof(motion_state_t),
    sizeof(door_def_t), sizeof(door_state_t)
};

void R_PlatformInit(void);
void R_ActorFrame(void);
void R_ActorInit(void);
void R_CombatInit(void);
uint8_t R_PlayerAlive(void);
void R_DrawCombatHUD(void);
__code __at(0xFFF0) const uint8_t renderer_format[] = {'D','8','0','5',5};
/* The renderer uses stack arguments; the non-reentrant cache uses ABI 1. */
void DdrWriteStack(uint32_t address, uint8_t value);
const texture_t *R_GetTexture(int16_t n) { return textures + n; }
static uint32_t pointer_address(const uint8_t *p)
{
    union { const uint8_t *p; uint8_t b[3]; } u;
    u.p = p;
    return ((uint32_t)u.b[2] << 16) | ((uint16_t)u.b[1] << 8) | u.b[0];
}
void R_PlatformTexture(int16_t n, int16_t col, draw_column_vars_t *dc)
{
    const texture_t *tex = textures + n;
    DdrLoadColumn(texture_pixels[n] + ((uint32_t)(col & tex->widthmask) << 7));
    DdrLoadColorMap(pointer_address(dc->colormap));
    R_DrawColumnWall(dc);
}

/* Column-major indexed storage makes each vertical draw contiguous in DDR. */
void R_DrawColumnWall(const draw_column_vars_t *dc)
{
    static int16_t count;
    count = dc->yh - dc->yl + 1;
    if (count <= 0) return;
    doom_column_frac = (dc->texturemid >> 7) + (dc->yl - VIEWWINDOWHEIGHT / 2) * dc->fracstep;
    doom_column_step = dc->fracstep;
    doom_draw_address = DOOM_INDEXED_BASE + dc->x * DOOM_TEXTURE_COLUMN_SIZE + dc->yl;
    doom_draw_count = count;
    DdrDrawColumn(1);
}
void R_DrawColumnFlat(uint8_t color, const draw_column_vars_t *dc)
{
    static int16_t count;
    count = dc->yh - dc->yl + 1;
    if (count <= 0) return;
    doom_draw_address = DOOM_INDEXED_BASE + dc->x * DOOM_TEXTURE_COLUMN_SIZE + dc->yl;
    doom_draw_count = count;
    doom_draw_color = color;
    DdrDrawColumn(0);
}
byte R_GetPlaneColor(int16_t picnum, int16_t lightlevel)
{
    return R_LoadColorMap(lightlevel)[picnum < 0 ? 122 : picnum];
}
void R_LoadSkyPatch(void) { }
void R_FreeSkyPatch(void) { }
void R_DrawSky(draw_column_vars_t *dc) { R_DrawColumnFlat(99, dc); }

void MotionSectorAt(int32_t x,int32_t y,int16_t *floor,int16_t *ceiling)
{
    sector_t *sector=R_PointInSubsector(x,y)->sector;
    *floor=sector->floorheight>>16;
    *ceiling=sector->ceilingheight>>16;
}

int16_t DoorSectorCeiling(uint16_t sector) {return _g_sectors[sector].ceilingheight>>16;}
void DoorSetCeiling(uint16_t sector,int16_t height) {_g_sectors[sector].ceilingheight=(int32_t)height*65536L;}

void main(void)
{
    static uint16_t i;
    static uint16_t frames;
    /* Match the SDK's _CKCON_MOVX_DEFAULT_CYCLE = _CKCON_MOVX_2_CYCLE. */
    doom_ckcon = (doom_ckcon & ~DOOM_MOVX_MASK) | DOOM_MOVX_DEFAULT;
    renderer_status[0] = 1;
    DdrInit();
    R_PlatformInit();
    _g_segs = DdrPointer(renderer_boot.segs);
    _g_sectors = DdrPointer(renderer_boot.sectors);
    _g_subsectors = DdrPointer(renderer_boot.subsectors);
    _g_lines = DdrPointer(renderer_boot.lines);
    _g_sides = DdrPointer(renderer_boot.sides);
    nodes = DdrPointer(renderer_boot.nodes);
    numnodes = renderer_boot.nodecount;
    _g_numsectors = renderer_boot.sectorcount;
    _g_numlines = renderer_boot.linecount;
    textures = DdrPointer(renderer_boot.textureinfo);
    texture_pixels = DdrPointer(renderer_boot.texturepixels);
    textureheight = DdrPointer(renderer_boot.heights);
    texturetranslation = DdrPointer(renderer_boot.translations);
    palette = DdrPointer(renderer_boot.palette);
    screen = DdrPointer(DOOM_INDEXED_BASE);
    for (i = 0; i != 256; ++i) {
        palette_xram[i] = palette[i * 3 + 2];
        palette_xram[i + 256] = palette[i * 3 + 1];
        palette_xram[i + 512] = palette[i * 3];
    }
    camera.x = renderer_boot.x;
    camera.y = renderer_boot.y;
    camera.angle = renderer_boot.angle;
    _g_player.mo = &camera;
    _g_player.viewz = renderer_boot.viewz;
    motion_state.x=camera.x;motion_state.y=camera.y;motion_state.angle=camera.angle;
    MotionSectorAt(camera.x,camera.y,(int16_t *)&motion_state.floor,(int16_t *)&motion_state.ceiling);
    MotionInit(renderer_boot.collisionlines,renderer_boot.blockmap,renderer_boot.linecount);
    DoorInit(renderer_boot.doors);
    R_ActorInit();
    R_CombatInit();
    frames = ((uint16_t)renderer_frames_hi<<8)|renderer_frames;
    if (!frames) frames = 1;
    do {
        renderer_status[0] = 2;
        if(R_PlayerAlive()) MotionFrame();
        else {motion_state.enabled=motion_input.enabled;motion_state.frame_ticks=0;}
        if(motion_state.enabled) {
            camera.x=motion_state.x;camera.y=motion_state.y;camera.angle=motion_state.angle;
            _g_player.viewz=((int32_t)motion_state.floor+MOTION_VIEW_HEIGHT)*65536L;
        }
        R_ActorFrame();
        renderer_status[0] = 4;
        DdrClearFrame();
        R_RenderPlayerView(&_g_player);
        R_DrawCombatHUD();
        renderer_status[0] = 3;
        DdrPresentFrame();
        DdrFlush();
        renderer_status[1] = ddr_fault ? ddr_fault : (motion_state.fault ? motion_state.fault : door_info.fault);
        if (--frames) {
            renderer_ack = 0;
            renderer_status[0] = 0xA4;
            while (!renderer_ack) { }
            ++_g_gametic;
            if(!motion_input.enabled) {camera.angle += renderer_angle_step;motion_state.angle=camera.angle;}
        } else renderer_status[0] = 0xA5;
    } while (frames);
    for (;;) { }
}
