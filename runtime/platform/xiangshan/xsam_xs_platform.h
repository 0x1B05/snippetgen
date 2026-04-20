#ifndef XSAM_XS_PLATFORM_H
#define XSAM_XS_PLATFORM_H

#include <stddef.h>
#include <stdint.h>

uint64_t xsam_xs_clint_mtime_addr(void);
uint64_t xsam_xs_clint_mtimecmp_addr(void);
uint64_t xsam_xs_clint_read_mtime(void);
uint64_t xsam_xs_clint_read_mtimecmp(void);
void xsam_xs_clint_write_mtimecmp(uint64_t value);
size_t xsam_xs_clint_read_uptime(uintptr_t reg, void *buf, size_t size);

enum {
  XSAM_XS_PMPCFG_BASE = 0x3a0,
  XSAM_XS_PMPADDR_BASE = 0x3b0,
  XSAM_XS_PMP_R = 0x1,
  XSAM_XS_PMP_W = 0x2,
  XSAM_XS_PMP_X = 0x4,
  XSAM_XS_PMP_A_TOR = 0x1,
  XSAM_XS_PMP_A_NA4 = 0x2,
  XSAM_XS_PMP_A_NAPOT = 0x3,
  XSAM_XS_PMP_COUNT = 16u,
};

size_t xsam_xs_serial_write(uintptr_t reg, const void *buf, size_t size);
size_t xsam_xs_input_read(uintptr_t reg, void *buf, size_t size);
size_t xsam_xs_perf_read(uintptr_t reg, void *buf, size_t size);

void xsam_xs_plic_init(void);
void xsam_xs_pma_init(void);
uint64_t xsam_xs_pmp_read_num(int csr_num);
void xsam_xs_pmp_write_num(int csr_num, uint64_t value);
void xsam_xs_pmp_set_num(int csr_num, uint64_t value);
void xsam_xs_pmp_clear_num(int csr_num, uint64_t value);
void xsam_xs_pmp_init(void);
void xsam_xs_pmp_enable_napot(
    uintptr_t pmp_reg,
    uintptr_t pmp_addr,
    uintptr_t pmp_size,
    int lock,
    uint8_t permission);
void xsam_xs_pmp_enable_tor(
    uintptr_t pmp_reg,
    uintptr_t pmp_addr,
    uintptr_t pmp_size,
    int lock,
    uint8_t permission);
void xsam_xs_pmp_disable(uintptr_t pmp_reg);
void xsam_xs_cache_init(void);

#endif
