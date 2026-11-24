/* Native MCU_DC transport for the fast core. Register addresses come from the
 * RTD2795T regdb via ddr_sim.py, not from a second hard-coded register map.
 * Layout: docs/ddr-draw.md (#255/#267), measured 2026-11-19/20.
 * Only the verified two-unit (16 byte) transaction is implemented. */
#define DDR_PORTS 2
#define DDR_UNIT_BYTES 8
#define DDR_BURST_BYTES 16
#define DDR_CMD_MASK 0xE0
#define DDR_WRITE 0x80
#define DDR_READ 0xA0
#define DDR_READY 1
enum { DDR_CMD, DDR_LEN, DDR_ADDR, DDR_WBUF, DDR_RBUF, DDR_MASK, DDR_FLAG, DDR_NREG };
enum { DDR_WRITES, DDR_READS, DDR_INVALID, DDR_HAZARDS, DDR_DROPPED, DDR_NSTAT };
typedef struct {
    uint16_t reg[DDR_NREG];
    uint64_t due, latency, stat[DDR_NSTAT];
    uint32_t addr, drop_every, read_seq;
    uint16_t mask;
    uint8_t op, data[DDR_BURST_BYTES];
} ddr_port_t;

/* Included inside core_t. */
#define DDR_CORE_FIELDS uint8_t *ddr; uint32_t ddr_size; ddr_port_t dp[DDR_PORTS];
