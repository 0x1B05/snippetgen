#include "xsrt_csr.h"

#include <stddef.h>

enum {
  XSRT_CSR_SHADOW_SIZE = 4096,
};

static uint64_t g_csr_shadow[XSRT_CSR_SHADOW_SIZE];

uint64_t xsrt_csr_read(uint32_t csr) {
  if (csr >= XSRT_CSR_SHADOW_SIZE) {
    return 0;
  }

  return g_csr_shadow[csr];
}

void xsrt_csr_write(uint32_t csr, uint64_t val) {
  if (csr >= XSRT_CSR_SHADOW_SIZE) {
    return;
  }

  g_csr_shadow[csr] = val;
}
