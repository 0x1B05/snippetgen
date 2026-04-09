#include <stdint.h>

#include "xs_snippet.h"
#include "xsrt_csr.h"


static int unaligned_load_run(xsrt_env_t *env) {
  static const uint8_t bytes[] = {0x00u, 0x78u, 0x56u, 0x34u, 0x12u, 0x00u};
  const uint8_t *ptr = &bytes[1];
  uint32_t value;

  if (env == 0) {
    return -1;
  }

#if defined(__riscv)
  __asm__ volatile(
      "lw %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
#else
  value = ((uint32_t) ptr[0]) |
          ((uint32_t) ptr[1] << 8) |
          ((uint32_t) ptr[2] << 16) |
          ((uint32_t) ptr[3] << 24);
#endif

  env->snippet_id = value;
  xsrt_csr_write(7u, value);
  return 0;
}


const xsrt_snippet_desc_t snippet_unaligned_load = {
  .id = "unaligned_load",
  .run = unaligned_load_run,
};
