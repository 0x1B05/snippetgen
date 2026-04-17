#include "xsam_noop_platform.h"

#include "xsam/amdev.h"

uint64_t xsam_noop_clint_read_mtime(void) {
  return 0u;
}

uint64_t xsam_noop_clint_read_mtimecmp(void) {
  return 0u;
}

void xsam_noop_clint_write_mtimecmp(uint64_t value) {
  (void) value;
}

size_t xsam_noop_clint_read_uptime(uintptr_t reg, void *buf, size_t size) {
  xsam_dev_timer_uptime_t *uptime;

  if (reg != XSAM_DEVREG_TIMER_UPTIME || buf == 0 || size < sizeof(*uptime)) {
    return 0;
  }

  uptime = (xsam_dev_timer_uptime_t *) buf;
  uptime->hi = 0u;
  uptime->lo = 0u;
  return sizeof(*uptime);
}
