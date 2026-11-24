#include "../fw/doom/motion.h"
#include "../fw/doom/doors.h"
volatile __xdata __at(0xF600) uint8_t status;
volatile __xdata __at(0xF620) uint8_t op;
volatile __xdata __at(0xF640) uint16_t count;
volatile __xdata __at(0xF642) int16_t floor_a;
volatile __xdata __at(0xF644) int16_t floor_b;
volatile __xdata __at(0xF646) int16_t ceiling_a;
volatile __xdata __at(0xF648) int16_t ceiling_b;
volatile __xdata __at(0xF64A) uint16_t initial_keys;
__xdata uint16_t doom_column_target,doom_column_frac,doom_column_step;
__xdata uint8_t doom_column_count;
int32_t finecosineapprox(int16_t angle) {
    switch((uint16_t)angle>>11){case 0:return 65536L;case 2:return -65536L;default:return 0;}
}
int32_t finesineapprox(int16_t angle) {
    switch((uint16_t)angle>>11){case 1:return 65536L;case 3:return -65536L;default:return 0;}
}
void MotionSectorAt(int32_t x,int32_t y,int16_t *floor,int16_t *ceiling) {
    y;
    *floor=x>=64L*65536L ? floor_b:floor_a;
    *ceiling=x>=64L*65536L ? ceiling_b:ceiling_a;
}
/* Force the same DDR-cache index as a profile, exercising pointer reacquire. */
int16_t DoorSectorCeiling(uint16_t sector){DdrRead(0x20010UL);return sector ? ceiling_b:ceiling_a;}
void DoorSetCeiling(uint16_t sector,int16_t height){if(sector)ceiling_b=height;else ceiling_a=height;}
volatile __xdata __at(0xF650) int16_t query[5];
volatile __xdata __at(0xF65A) uint8_t result;
volatile __xdata __at(0xF65C) int16_t query_floor_result;
static uint8_t body(int16_t x,int16_t y){y;return x>=64;}
static uint8_t door_body(const door_def_t *door,int16_t next){door;return next<56;}
void main(void) {
    DdrInit();
    motion_state.floor=floor_a;motion_state.ceiling=ceiling_a;
    MotionInit(MOTION_LINES_BASE,MOTION_BLOCKMAP_BASE,count);
    DoorInit(DOOR_DATA_BASE);
    key_info[0]=initial_keys;
    status=0xA5;
    for(;;) {
        if(op==1){MotionFrame();DdrFlush();op=0;}
        else if(op==2){result=MotionActorMove(query[0],query[1],query[2]);query_floor_result=motion_actor_floor;DdrFlush();op=0;}
        else if(op==3){result=MotionVisible(query[0],query[1],query[2],query[3],query[4]);op=0;}
        else if(op==4){MotionSetThingsBlock(body);op=0;}
        else if(op==5){DoorSetThingsBlock(door_body);op=0;}
    }
}
