/* Standalone player-motion bring-up, not the original Doom thinker/physics. */
#ifndef DOOM_MOTION_H
#define DOOM_MOTION_H
#include "platform.h"
#define MOTION_INPUT_BASE 0xF610
#define MOTION_STATE_BASE 0xF6A0
#define MOTION_LINES_BASE 0x00080010UL
#define MOTION_BLOCKMAP_BASE 0x00090010UL
#define MOTION_LINE_LIMIT 512
#define MOTION_PLAYER_RADIUS 16
#define MOTION_PLAYER_HEIGHT 56
#define MOTION_STEP_HEIGHT 24
#define MOTION_COMMAND_LIMIT 8
#define MOTION_TURN_LIMIT 4096
#define MOTION_TICK_HZ 35
#define MOTION_FRAME_HZ 25
#define MOTION_VIEW_HEIGHT 41
#define MOTION_LINE_SOLID 1
#define MOTION_LINE_HEIGHT_CHANGE 2

typedef struct {
    int16_t x1,y1,x2,y2,bottom,top;
    uint8_t flags,front,back,use;
} motion_line_t;
typedef struct {
    int8_t forward,strafe;
    int16_t turn;
    uint8_t enabled,buttons;
} motion_input_t;
typedef struct {
    int32_t x,y;
    uint32_t angle;
    int16_t floor,ceiling;
    uint32_t ticks;
    uint8_t blocked,frame_ticks,fault,enabled;
} motion_state_t;
extern volatile __xdata __at(MOTION_INPUT_BASE) motion_input_t motion_input;
extern volatile __xdata __at(MOTION_STATE_BASE) motion_state_t motion_state;
void MotionInit(uint32_t lines,uint32_t blockmap,uint16_t count);
void MotionFrame(void);
uint8_t MotionActorMove(int16_t x,int16_t y,int16_t floor);
uint8_t MotionVisible(int16_t x,int16_t y,int16_t endx,int16_t endy,int16_t eye);
extern int16_t motion_actor_floor;
void MotionSetThingsBlock(uint8_t (*check)(int16_t,int16_t));
uint8_t MotionTraceUse(int16_t end_x,int16_t end_y);
void MotionRefreshLine(uint16_t line);
void MotionWorldChanged(void);
void MotionSectorAt(int32_t x,int32_t y,int16_t *floor,int16_t *ceiling);
#endif
