#include "xsam_noop_platform.h"

#include "xsam/amdev.h"

size_t xsam_noop_serial_write(uintptr_t reg, const void *buf, size_t size) {
  if (reg != XSAM_DEVREG_SERIAL_SEND || buf == 0 || size < sizeof(xsam_dev_serial_send_t)) {
    return 0;
  }
  return sizeof(xsam_dev_serial_send_t);
}
