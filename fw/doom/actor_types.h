#ifndef DOOM_ACTOR_TYPES_H
#define DOOM_ACTOR_TYPES_H
#include "platform.h"
typedef struct { int16_t x,y; uint16_t angle,kind; int32_t depth; uint16_t tics; uint8_t frame,awake; int16_t floor; uint16_t health; } static_thing_t;
typedef struct {
    int16_t width,height,left,top;
    uint32_t pixels;
    uint8_t flip,reserved[3];
} static_patch_t;
#endif
