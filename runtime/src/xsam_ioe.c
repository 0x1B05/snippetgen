#include "xsam/ioe.h"

#include "xsam_xs_platform.h"

int xsam_ioe_init(void) {
  xsam_xs_plic_init();
  xsam_xs_pma_init();
  xsam_xs_pmp_init();
  xsam_xs_cache_init();
  return 0;
}

size_t xsam_io_read(uint32_t dev, uintptr_t reg, void *buf, size_t size) {
  switch (dev) {
    case XSAM_DEV_TIMER:
      return xsam_xs_clint_read_uptime(reg, buf, size);
    case XSAM_DEV_INPUT:
      return xsam_xs_input_read(reg, buf, size);
    case XSAM_DEV_PERFCNT:
      return xsam_xs_perf_read(reg, buf, size);
    default:
      return 0;
  }
}

size_t xsam_io_write(uint32_t dev, uintptr_t reg, const void *buf, size_t size) {
  switch (dev) {
    case XSAM_DEV_SERIAL:
      return xsam_xs_serial_write(reg, buf, size);
    default:
      return 0;
  }
}
