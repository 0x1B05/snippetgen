#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_load_arena[256] __attribute__((aligned(16)));

static uint32_t xs_scalar_misalign_lw(const void *ptr) {
  uint32_t value;

  __asm__ volatile(
      "lw %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static uint64_t xs_scalar_misalign_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static void xs_scalar_misalign_fill_le(uint8_t *ptr, uint64_t value, unsigned width) {
  for (unsigned index = 0; index < width; ++index) {
    ptr[index] = (uint8_t) (value >> (8u * index));
  }
}

static void xs_scalar_misalign_zero_region(uint8_t *base, unsigned size) {
  for (unsigned index = 0; index < size; ++index) {
    base[index] = 0u;
  }
}

static int xs_scalar_misalign_check_lw_case(uint8_t *base, unsigned offset, uint32_t expected, int fail_code) {
  const uint8_t *ptr = base + offset;

  xs_scalar_misalign_zero_region(base, 32u);
  xs_scalar_misalign_fill_le((uint8_t *) ptr, expected, 4u);
  if (xs_scalar_misalign_lw(ptr) != expected) {
    xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, (uint64_t) fail_code);
    return fail_code;
  }
  return 0;
}

static int xs_scalar_misalign_check_ld_case(uint8_t *base, unsigned offset, uint64_t expected, int fail_code) {
  const uint8_t *ptr = base + offset;

  xs_scalar_misalign_zero_region(base, 32u);
  xs_scalar_misalign_fill_le((uint8_t *) ptr, expected, 8u);
  if (xs_scalar_misalign_ld(ptr) != expected) {
    xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, (uint64_t) fail_code);
    return fail_code;
  }
  return 0;
}

static int load_split_templates_run(xsrt_env_t *env) {
  int rc;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);

  rc = xs_scalar_misalign_check_lw_case(&xs_scalar_misalign_load_arena[0], 13u, 0x11223344u, 301);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_lw_case(&xs_scalar_misalign_load_arena[32], 14u, 0x22334455u, 302);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_lw_case(&xs_scalar_misalign_load_arena[64], 15u, 0x33445566u, 303);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_ld_case(&xs_scalar_misalign_load_arena[96], 9u, 0x1122334455667788ull, 304);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_ld_case(&xs_scalar_misalign_load_arena[128], 12u, 0x2233445566778899ull, 305);
  if (rc != 0) {
    return rc;
  }
  rc = xs_scalar_misalign_check_ld_case(&xs_scalar_misalign_load_arena[160], 15u, 0x33445566778899aaull, 306);
  if (rc != 0) {
    return rc;
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 6u);
  env->snippet_id = XS_SCALAR_MISALIGN_LOAD_SPLIT_MAGIC ^ 6u;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_load_split_templates = {
  .id = "load_split_templates",
  .run = load_split_templates_run,
};
