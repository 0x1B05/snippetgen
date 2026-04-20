#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_store_arena[256] __attribute__((aligned(16)));

static void xs_scalar_misalign_sw(void *ptr, uint32_t value) {
  __asm__ volatile(
      "sw %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static void xs_scalar_misalign_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static void xs_scalar_misalign_zero_region(uint8_t *base, unsigned size) {
  for (unsigned index = 0; index < size; ++index) {
    base[index] = 0u;
  }
}

static int xs_scalar_misalign_check_bytes(const uint8_t *ptr, uint64_t expected, unsigned width, int fail_code) {
  for (unsigned index = 0; index < width; ++index) {
    if (ptr[index] != (uint8_t) (expected >> (8u * index))) {
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, (uint64_t) fail_code);
      return fail_code;
    }
  }
  return 0;
}

static int xs_scalar_misalign_check_sw_case(uint8_t *base, unsigned offset, uint32_t expected, int fail_code) {
  uint8_t *ptr = base + offset;

  xs_scalar_misalign_zero_region(base, 32u);
  xs_scalar_misalign_sw(ptr, expected);
  return xs_scalar_misalign_check_bytes(ptr, expected, 4u, fail_code);
}

static int xs_scalar_misalign_check_sd_case(uint8_t *base, unsigned offset, uint64_t expected, int fail_code) {
  uint8_t *ptr = base + offset;

  xs_scalar_misalign_zero_region(base, 32u);
  xs_scalar_misalign_sd(ptr, expected);
  return xs_scalar_misalign_check_bytes(ptr, expected, 8u, fail_code);
}

static int store_split_templates_run(xsrt_env_t *env) {
  int rc;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);

  rc = xs_scalar_misalign_check_sw_case(&xs_scalar_misalign_store_arena[0], 13u, 0x11223344u, 311);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_sw_case(&xs_scalar_misalign_store_arena[32], 14u, 0x22334455u, 312);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_sw_case(&xs_scalar_misalign_store_arena[64], 15u, 0x33445566u, 313);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_sd_case(&xs_scalar_misalign_store_arena[96], 9u, 0x1122334455667788ull, 314);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_sd_case(&xs_scalar_misalign_store_arena[128], 12u, 0x2233445566778899ull, 315);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_sd_case(&xs_scalar_misalign_store_arena[160], 15u, 0x33445566778899aaull, 316);
  if (rc != 0) {
    return rc;
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 6u);
  env->snippet_id = XS_SCALAR_MISALIGN_STORE_SPLIT_MAGIC ^ 6u;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_store_split_templates = {
  .id = "store_split_templates",
  .run = store_split_templates_run,
};
