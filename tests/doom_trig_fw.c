#include "../fw/doom/platform.h"
volatile __xdata __at(0xF600) uint8_t status;
volatile __xdata __at(0xF620) uint16_t angle;
volatile __xdata __at(0xF624) int32_t sine;
volatile __xdata __at(0xF628) int32_t cosine;
volatile __xdata __at(0xF62C) uint8_t op;
__xdata uint16_t doom_column_target,doom_column_frac,doom_column_step;
__xdata uint8_t doom_column_count;
int32_t finesineapprox(int16_t x);
int32_t finecosineapprox(int16_t x);
void main(void) {DdrInit();status=0xA5;for(;;)if(op){sine=finesineapprox(angle);cosine=finecosineapprox(angle);op=0;}}
