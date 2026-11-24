#ifndef DOOM_ACTOR_TYPES_H
#define DOOM_ACTOR_TYPES_H
#include "platform.h"
typedef struct { int16_t x,y; uint16_t angle,kind; int32_t depth; uint16_t tics; uint8_t frame,awake; int16_t floor; uint16_t health; } static_thing_t;
typedef struct {
    int16_t width,height,left,top;
    uint32_t pixels;
    uint8_t flip,reserved[3];
} static_patch_t;
typedef struct {
    uint16_t health,ammo,shots,hits,kills,damage,attacks,dead;
    uint8_t wait,flash,hurt,spare;
    uint16_t target;
} combat_state_t;
#define DOOM_PICKUP_HEADER_BASE 0xD8010UL
#define DOOM_PICKUP_MAX 128
#define DOOM_PICKUP_RULES 11
#define DOOM_FIRST_KEY_RULE 5
#define DOOM_PICKUP_RADIUS 20
#define DOOM_PICKUP_FLASH_TICKS 5
#define DOOM_NORMAL_HEALTH 100
#define DOOM_BONUS_HEALTH 200
#define DOOM_MAX_BULLETS 200
#endif
