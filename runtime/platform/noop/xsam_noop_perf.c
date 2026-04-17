#include "xsam_noop_platform.h"

#include <stdint.h>

size_t xsam_noop_perf_read(uintptr_t reg, void *buf, size_t size) {
  uint64_t *counter;

  if (reg != 1u || buf == 0 || size < sizeof(*counter)) {
    return 0;
  }

  counter = (uint64_t *) buf;
  *counter = 0u;
  return sizeof(*counter);
}
