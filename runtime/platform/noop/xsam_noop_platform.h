#ifndef XSAM_NOOP_PLATFORM_H
#define XSAM_NOOP_PLATFORM_H

#include <stddef.h>
#include <stdint.h>

uint64_t xsam_noop_clint_read_mtime(void);
uint64_t xsam_noop_clint_read_mtimecmp(void);
void xsam_noop_clint_write_mtimecmp(uint64_t value);
size_t xsam_noop_clint_read_uptime(uintptr_t reg, void *buf, size_t size);
size_t xsam_noop_serial_write(uintptr_t reg, const void *buf, size_t size);
size_t xsam_noop_input_read(uintptr_t reg, void *buf, size_t size);
size_t xsam_noop_perf_read(uintptr_t reg, void *buf, size_t size);
void xsam_noop_plic_init(void);

#endif
