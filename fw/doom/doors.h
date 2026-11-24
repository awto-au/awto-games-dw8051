/* Standalone manual doors and key inventory. Not original sector thinkers. */
#ifndef DOOM_DOORS_H
#define DOOM_DOORS_H
#include "motion.h"
#define DOOR_DATA_BASE 0x000A0010UL
#define DOOR_STATE_BASE 0xF200
#define DOOR_INFO_BASE 0xF6C0
#define DOOR_LIMIT 32
#define DOOR_ACTION_BASE 0x000A6010UL
#define DOOR_ACTION_SWITCH 512
#define DOOR_ACTION_REPEAT 1024
#define DOOR_ACTION_STAY 256
#define DOOR_ACTION_ID_MASK 63
#define DOOR_ACTION_KEY_SHIFT 6
#define DOOR_USE_RANGE 64
#define DOOR_SPEED 2
#define DOOR_WAIT_TICKS 150
#define DOOR_CLOSED 0
#define DOOR_OPENING 1
#define DOOR_WAITING 2
#define DOOR_CLOSING 3
#define DOOR_OPEN_STAY 4
#define DOOR_USE_BUTTON 1
#define DOOR_STAY_TOKEN 128
#define DOOR_ID_MASK 31
#define DOOR_KEY_SHIFT 5
#define KEY_INFO_BASE 0xF748
#define KEY_NOTICE_TICKS 35
#define KEY_BLUE_MASK 9
#define KEY_YELLOW_MASK 18
#define KEY_RED_MASK 36
#define SWITCH_DATA_BASE 0x000A4010UL
#define SWITCH_INFO_BASE 0xF750
#define SWITCH_TIMER_BASE 0xF760
#define SWITCH_LIMIT 15
#define SWITCH_FIRST_TOKEN 17
#define SWITCH_REPEAT_TOKEN 32
#define SWITCH_RESET_TICKS 35
#define EXIT_INFO_BASE 0xF770
#define EXIT_NORMAL 1
#define EXIT_SECRET 2
typedef struct {
    uint32_t targets;
    uint16_t line;
    uint32_t texture;
    int16_t off,on;
    uint16_t kind;
} switch_def_t;

typedef struct {
    uint16_t sector;
    int16_t closed,top;
    uint16_t first,count;
    int16_t minx,maxx,miny,maxy;
    uint8_t reserved[14];
} door_def_t;
typedef struct {
    int16_t height;
    uint16_t wait;
    uint8_t phase,stay;
    uint16_t reserved;
} door_state_t;
typedef struct {
    uint8_t count,last_used,reopens,fault;
    uint16_t activations,updates;
} door_info_t;
extern __xdata __at(DOOR_STATE_BASE) door_state_t door_states[DOOR_LIMIT];
extern volatile __xdata __at(DOOR_INFO_BASE) door_info_t door_info;
/* Owned keys, required colour, rejected-use count, notice ticks. */
extern volatile __xdata __at(KEY_INFO_BASE) uint16_t key_info[4];
extern volatile __xdata __at(SWITCH_INFO_BASE) uint16_t switch_info[4];
extern __xdata __at(SWITCH_TIMER_BASE) uint8_t switch_timers[SWITCH_LIMIT];
extern volatile __xdata __at(EXIT_INFO_BASE) uint16_t exit_info[4];
void DoorInit(uint32_t data);
void DoorTick(void);
void DoorSetThingsBlock(uint8_t (*check)(const door_def_t *,int16_t));
int16_t DoorSectorCeiling(uint16_t sector);
void DoorSetCeiling(uint16_t sector,int16_t height);
#endif
