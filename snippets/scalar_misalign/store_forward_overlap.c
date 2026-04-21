#include <stddef.h>
#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_forward_arena[1024] __attribute__((aligned(64)));

static unsigned long xs_scalar_misalign_forward_skid(unsigned long lane, unsigned long count) {
  for (unsigned long index = 0; index < count; ++index) {
    __asm__ volatile(
        "addi %[lane], %[lane], 9\n"
        "xori %[lane], %[lane], 13\n"
        "andi %[lane], %[lane], 255\n"
        : [lane] "+r"(lane)
        :
        : "memory");
  }
  return lane;
}

static void xs_scalar_misalign_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
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

static uint32_t xs_scalar_misalign_lwu(const void *ptr) {
  uint32_t value;

  __asm__ volatile(
      "lwu %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static void xs_scalar_misalign_zero_region(uint8_t *base, unsigned size) {
  for (unsigned index = 0; index < size; ++index) {
    base[index] = 0u;
  }
}

static unsigned xs_scalar_misalign_forward_rounds(uint64_t seed) {
  return 2u + (unsigned) ((seed >> 8) & 0x3u);
}

static unsigned xs_scalar_misalign_forward_pair_seed(uint64_t seed) {
  return (unsigned) ((seed >> 2) & 0x3u);
}

static unsigned xs_scalar_misalign_forward_pre_stride(uint64_t seed) {
  return 1u + (unsigned) (seed & 0x7u);
}

static unsigned xs_scalar_misalign_forward_between_stride(uint64_t seed) {
  return 1u + (unsigned) ((seed >> 5) & 0x7u);
}

static uint64_t xs_scalar_misalign_forward_summary(uint64_t seed) {
  const unsigned rounds = xs_scalar_misalign_forward_rounds(seed);
  const unsigned pair_seed = xs_scalar_misalign_forward_pair_seed(seed);
  const unsigned pre_stride = xs_scalar_misalign_forward_pre_stride(seed);
  const unsigned between_stride = xs_scalar_misalign_forward_between_stride(seed);

  return ((uint64_t) XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC << 32) |
      ((uint64_t) between_stride << 24) |
      ((uint64_t) pre_stride << 16) |
      ((uint64_t) pair_seed << 8) |
      (uint64_t) rounds;
}

static uint64_t xs_scalar_misalign_target_value(uint64_t seed, unsigned round) {
  uint64_t value = 0x8877665544332211ull;

  value ^= ((uint64_t) (seed & 0xffu)) << 8;
  value ^= ((uint64_t) ((seed >> 8) & 0xffu)) << 24;
  value ^= (uint64_t) round << 40;
  return value;
}

static uint64_t xs_scalar_misalign_blocker_value(uint64_t seed, unsigned round) {
  uint64_t value = 0x1020304050607080ull;

  value ^= ((uint64_t) ((seed >> 16) & 0xffu)) << 16;
  value ^= (uint64_t) round << 48;
  return value;
}

static int store_forward_overlap_run(xsrt_env_t *env) {
  const unsigned rounds = xs_scalar_misalign_forward_rounds(env != 0 ? env->seed : 0u);
  const unsigned pair_seed = xs_scalar_misalign_forward_pair_seed(env != 0 ? env->seed : 0u);
  const unsigned pre_stride = xs_scalar_misalign_forward_pre_stride(env != 0 ? env->seed : 0u);
  const unsigned between_stride = xs_scalar_misalign_forward_between_stride(env != 0 ? env->seed : 0u);
  unsigned long lane;
  uint64_t value0;
  uint64_t value1;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY, 0u);

  xs_scalar_misalign_zero_region(xs_scalar_misalign_forward_arena, sizeof(xs_scalar_misalign_forward_arena));
  lane = (unsigned long) (env->seed | 1u);

  for (unsigned round = 0; round < rounds; ++round) {
    const unsigned pair_index = (pair_seed + round) & 0x3u;
    const uint64_t target_value = xs_scalar_misalign_target_value(env->seed, round);
    const uint64_t blocker_value = xs_scalar_misalign_blocker_value(env->seed, round);
    const uint32_t expected_high_word = (uint32_t) ((target_value >> 8) & 0xffffffffu);
    uint8_t *slot_a = &xs_scalar_misalign_forward_arena[pair_index * 256u];
    uint8_t *slot_b = slot_a + 128u;
    uint8_t *store_ptr = slot_a + 63u;
    uint8_t *fragment_ptr = slot_a + 64u;
    uint8_t *blocker_ptr = slot_b + 63u;
    uint32_t high_word;

    xs_scalar_misalign_zero_region(slot_a, 256u);
    lane = xs_scalar_misalign_forward_skid(lane, pre_stride + round);
    xs_scalar_misalign_sd(store_ptr, target_value);
    value0 = xs_scalar_misalign_ld(store_ptr);
    high_word = xs_scalar_misalign_lwu(fragment_ptr);
    lane = xs_scalar_misalign_forward_skid(lane, between_stride + (round & 0x1u));
    xs_scalar_misalign_sd(blocker_ptr, blocker_value);
    value1 = xs_scalar_misalign_ld(store_ptr);

    if (value0 != target_value) {
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 331u + (uint64_t) (round * 3u));
      return XS_SCALAR_MISALIGN_RC_STORE_FORWARD;
    }

    if (high_word != expected_high_word) {
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 332u + (uint64_t) (round * 3u));
      return XS_SCALAR_MISALIGN_RC_STORE_FORWARD + 1;
    }

    if (value1 != target_value) {
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 333u + (uint64_t) (round * 3u));
      return XS_SCALAR_MISALIGN_RC_STORE_FORWARD + 2;
    }
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0, value0);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1, value1);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY, xs_scalar_misalign_forward_summary(env->seed));
  env->snippet_id = XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC ^ (uint64_t) rounds;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_store_forward_overlap = {
  .id = "store_forward_overlap",
  .run = store_forward_overlap_run,
};
