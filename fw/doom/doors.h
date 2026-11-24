/* Standalone unlocked manual doors. Not the original Doom sector thinkers. */
#ifndef DOOM_DOORS_H
#define DOOM_DOORS_H
#include "motion.h"
#define DOOR_DATA_BASE 0x000A0010UL
#define DOOR_STATE_BASE 0xF200
#define DOOR_INFO_BASE 0xF6C0
#define DOOR_LIMIT 16
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
void DoorInit(uint32_t data);
void DoorTick(void);
void DoorSetThingsBlock(uint8_t (*check)(const door_def_t *,int16_t));
int16_t DoorSectorCeiling(uint16_t sector);
void DoorSetCeiling(uint16_t sector,int16_t height);
#endif
