#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_load_arena[256] __attribute__((aligned(16)));

enum {
  XS_SCALAR_MISALIGN_TEMPLATE_SLOT_SIZE = 32u,
  XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT = 8u,
  XS_SCALAR_MISALIGN_LOAD_CASE_COUNT = 6u,
};

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

static unsigned xs_scalar_misalign_load_rounds(uint64_t seed) {
  return 2u + (unsigned) ((seed >> 5) & 0x3u);
}

static unsigned xs_scalar_misalign_load_rotation(uint64_t seed) {
  return (unsigned) ((seed ^ (seed >> 7)) % XS_SCALAR_MISALIGN_LOAD_CASE_COUNT);
}

static unsigned xs_scalar_misalign_load_bank_seed(uint64_t seed) {
  return (unsigned) ((seed >> 3) & (XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT - 1u));
}

static uint64_t xs_scalar_misalign_load_summary(uint64_t seed) {
  const unsigned rounds = xs_scalar_misalign_load_rounds(seed);
  const unsigned rotation = xs_scalar_misalign_load_rotation(seed);
  const unsigned bank_seed = xs_scalar_misalign_load_bank_seed(seed);
  const unsigned total_cases = rounds * XS_SCALAR_MISALIGN_LOAD_CASE_COUNT;

  return ((uint64_t) XS_SCALAR_MISALIGN_LOAD_SPLIT_MAGIC << 32) |
      ((uint64_t) rounds << 24) |
      ((uint64_t) bank_seed << 16) |
      ((uint64_t) rotation << 8) |
      (uint64_t) total_cases;
}

static int xs_scalar_misalign_run_load_case(unsigned case_index, uint8_t *base) {
  switch (case_index) {
    case 0:
      return xs_scalar_misalign_check_lw_case(base, 13u, 0x11223344u, 301);
    case 1:
      return xs_scalar_misalign_check_lw_case(base, 14u, 0x22334455u, 302);
    case 2:
      return xs_scalar_misalign_check_lw_case(base, 15u, 0x33445566u, 303);
    case 3:
      return xs_scalar_misalign_check_ld_case(base, 9u, 0x1122334455667788ull, 304);
    case 4:
      return xs_scalar_misalign_check_ld_case(base, 12u, 0x2233445566778899ull, 305);
    case 5:
      return xs_scalar_misalign_check_ld_case(base, 15u, 0x33445566778899aaull, 306);
    default:
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 307u);
      return 307;
  }
}

static int load_split_templates_run(xsrt_env_t *env) {
  const unsigned rounds = xs_scalar_misalign_load_rounds(env != 0 ? env->seed : 0u);
  const unsigned rotation = xs_scalar_misalign_load_rotation(env != 0 ? env->seed : 0u);
  const unsigned bank_seed = xs_scalar_misalign_load_bank_seed(env != 0 ? env->seed : 0u);
  int rc;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_LOAD_SPLIT_SUMMARY, 0u);

  for (unsigned round = 0; round < rounds; ++round) {
    for (unsigned slot = 0; slot < XS_SCALAR_MISALIGN_LOAD_CASE_COUNT; ++slot) {
      const unsigned case_index = (rotation + round + slot) % XS_SCALAR_MISALIGN_LOAD_CASE_COUNT;
      const unsigned bank = (bank_seed + slot + (round * 3u)) & (XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT - 1u);
      uint8_t *base = &xs_scalar_misalign_load_arena[bank * XS_SCALAR_MISALIGN_TEMPLATE_SLOT_SIZE];

      rc = xs_scalar_misalign_run_load_case(case_index, base);
      if (rc != 0) {
        return rc;
      }
    }
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, (uint64_t) (rounds * XS_SCALAR_MISALIGN_LOAD_CASE_COUNT));
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_LOAD_SPLIT_SUMMARY, xs_scalar_misalign_load_summary(env->seed));
  env->snippet_id = XS_SCALAR_MISALIGN_LOAD_SPLIT_MAGIC ^ (uint64_t) (rounds * XS_SCALAR_MISALIGN_LOAD_CASE_COUNT);
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_load_split_templates = {
  .id = "load_split_templates",
  .run = load_split_templates_run,
};
