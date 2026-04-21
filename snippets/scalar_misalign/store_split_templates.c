#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_store_arena[256] __attribute__((aligned(16)));

enum {
  XS_SCALAR_MISALIGN_TEMPLATE_SLOT_SIZE = 32u,
  XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT = 8u,
  XS_SCALAR_MISALIGN_STORE_CASE_COUNT = 6u,
};

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

static unsigned xs_scalar_misalign_store_rounds(uint64_t seed) {
  return 2u + (unsigned) ((seed >> 12) & 0x3u);
}

static unsigned xs_scalar_misalign_store_rotation(uint64_t seed) {
  return (unsigned) (((seed >> 7) ^ seed) % XS_SCALAR_MISALIGN_STORE_CASE_COUNT);
}

static unsigned xs_scalar_misalign_store_bank_seed(uint64_t seed) {
  return (unsigned) ((seed >> 10) & (XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT - 1u));
}

static uint64_t xs_scalar_misalign_store_summary(uint64_t seed) {
  const unsigned rounds = xs_scalar_misalign_store_rounds(seed);
  const unsigned rotation = xs_scalar_misalign_store_rotation(seed);
  const unsigned bank_seed = xs_scalar_misalign_store_bank_seed(seed);
  const unsigned total_cases = rounds * XS_SCALAR_MISALIGN_STORE_CASE_COUNT;

  return ((uint64_t) XS_SCALAR_MISALIGN_STORE_SPLIT_MAGIC << 32) |
      ((uint64_t) rounds << 24) |
      ((uint64_t) bank_seed << 16) |
      ((uint64_t) rotation << 8) |
      (uint64_t) total_cases;
}

static int xs_scalar_misalign_run_store_case(unsigned case_index, uint8_t *base) {
  switch (case_index) {
    case 0:
      return xs_scalar_misalign_check_sw_case(base, 13u, 0x11223344u, 311);
    case 1:
      return xs_scalar_misalign_check_sw_case(base, 14u, 0x22334455u, 312);
    case 2:
      return xs_scalar_misalign_check_sw_case(base, 15u, 0x33445566u, 313);
    case 3:
      return xs_scalar_misalign_check_sd_case(base, 9u, 0x1122334455667788ull, 314);
    case 4:
      return xs_scalar_misalign_check_sd_case(base, 12u, 0x2233445566778899ull, 315);
    case 5:
      return xs_scalar_misalign_check_sd_case(base, 15u, 0x33445566778899aaull, 316);
    default:
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 317u);
      return 317;
  }
}

static int store_split_templates_run(xsrt_env_t *env) {
  const unsigned rounds = xs_scalar_misalign_store_rounds(env != 0 ? env->seed : 0u);
  const unsigned rotation = xs_scalar_misalign_store_rotation(env != 0 ? env->seed : 0u);
  const unsigned bank_seed = xs_scalar_misalign_store_bank_seed(env != 0 ? env->seed : 0u);
  int rc;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_STORE_SPLIT_SUMMARY, 0u);

  for (unsigned round = 0; round < rounds; ++round) {
    for (unsigned slot = 0; slot < XS_SCALAR_MISALIGN_STORE_CASE_COUNT; ++slot) {
      const unsigned case_index = (rotation + (round * 2u) + slot) % XS_SCALAR_MISALIGN_STORE_CASE_COUNT;
      const unsigned bank = (bank_seed + slot + round) & (XS_SCALAR_MISALIGN_TEMPLATE_SLOT_COUNT - 1u);
      uint8_t *base = &xs_scalar_misalign_store_arena[bank * XS_SCALAR_MISALIGN_TEMPLATE_SLOT_SIZE];

      rc = xs_scalar_misalign_run_store_case(case_index, base);
      if (rc != 0) {
        return rc;
      }
    }
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT, (uint64_t) (rounds * XS_SCALAR_MISALIGN_STORE_CASE_COUNT));
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_STORE_SPLIT_SUMMARY, xs_scalar_misalign_store_summary(env->seed));
  env->snippet_id = XS_SCALAR_MISALIGN_STORE_SPLIT_MAGIC ^ (uint64_t) (rounds * XS_SCALAR_MISALIGN_STORE_CASE_COUNT);
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_store_split_templates = {
  .id = "store_split_templates",
  .run = store_split_templates_run,
};
