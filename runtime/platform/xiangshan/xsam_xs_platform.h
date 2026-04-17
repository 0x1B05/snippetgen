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

size_t xsam_xs_serial_write(uintptr_t reg, const void *buf, size_t size);
size_t xsam_xs_input_read(uintptr_t reg, void *buf, size_t size);
size_t xsam_xs_perf_read(uintptr_t reg, void *buf, size_t size);

void xsam_xs_plic_init(void);
void xsam_xs_pma_init(void);
void xsam_xs_pmp_init(void);
void xsam_xs_cache_init(void);

#endif
