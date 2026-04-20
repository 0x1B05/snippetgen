#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_forward_search_arena[32768] __attribute__((aligned(64)));

static unsigned long xs_scalar_misalign_skid(unsigned long lane, unsigned long count) {
  for (unsigned long index = 0; index < count; ++index) {
    __asm__ volatile(
        "addi %[lane], %[lane], 3\n"
        "xori %[lane], %[lane], 11\n"
        "andi %[lane], %[lane], 255\n"
        : [lane] "+r"(lane)
        :
        : "memory");
  }
  return lane;
}

static void xs_scalar_misalign_write64(uint8_t *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %0, 0(%1)"
      :
      : "r"(value), "r"(ptr)
      : "memory");
}

static void xs_scalar_misalign_fill_burst(uint8_t *fill_base) {
  static const uint64_t kFillValue = 0x13579bdf2468ace0ull;

  for (unsigned long offset = 0; offset < 16u; ++offset) {
    xs_scalar_misalign_write64(fill_base + 64u * offset, kFillValue ^ (offset << 8));
  }
}

static void xs_scalar_misalign_probe_high_fragment(
    const uint8_t *fragment_base,
    uint32_t *word32,
    uint16_t *half16,
    uint8_t *byte8) {
  unsigned long word_value;
  unsigned long half_value;
  unsigned long byte_value;

  __asm__ volatile(
      "lwu %0, 0(%3)\n"
      "lhu %1, 4(%3)\n"
      "lbu %2, 6(%3)\n"
      : "=&r"(word_value), "=&r"(half_value), "=&r"(byte_value)
      : "r"(fragment_base)
      : "memory");
  *word32 = (uint32_t) word_value;
  *half16 = (uint16_t) half_value;
  *byte8 = (uint8_t) byte_value;
}

static void xs_scalar_misalign_zero_target_region(uint8_t *low_word_base, uint8_t *high_word_base) {
  *(uint64_t *) low_word_base = 0u;
  *(uint64_t *) high_word_base = 0u;
}

static int store_forward_search_run(xsrt_env_t *env) {
  static const uint64_t kTargetValue = 0x8877665544332211ull;
  static const uint64_t kBlockerValue = 0x00ffeeddccbbaa99ull;
  static const uint32_t kExpectedWord32 = 0x55443322u;
  static const uint16_t kExpectedHalf16 = 0x7766u;
  static const uint8_t kExpectedByte8 = 0x88u;
  unsigned long lane;
  unsigned long repeat_count;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_SEARCH_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE0, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE1, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE2, 0u);

  lane = (unsigned long) (env->seed | 1u);
  repeat_count = 3u + (unsigned long) ((env->seed >> 16) & 0x3u);

  for (unsigned long round = 0; round < repeat_count; ++round) {
    uint8_t *slot_base;
    uint8_t *target_base_a;
    uint8_t *fragment_base_a;
    uint8_t *target_ptr_a;
    uint8_t *target_base_b;
    uint8_t *fragment_base_b;
    uint8_t *target_ptr_b;
    uint8_t *fill_base;
    uint32_t probe_word32;
    uint16_t probe_half16;
    uint8_t probe_byte8;

    slot_base = &xs_scalar_misalign_forward_search_arena[4096u * ((round + (unsigned long) (env->seed >> 24)) & 0x7u)];
    target_base_a = slot_base;
    fragment_base_a = target_base_a + 64u;
    target_ptr_a = fragment_base_a - 1u;
    target_base_b = slot_base + 2048u;
    fragment_base_b = target_base_b + 64u;
    target_ptr_b = fragment_base_b - 1u;
    fill_base = target_base_a + 128u;

    xs_scalar_misalign_zero_target_region(target_base_a + 56u, fragment_base_a);
    xs_scalar_misalign_zero_target_region(target_base_b + 56u, fragment_base_b);
    xs_scalar_misalign_fill_burst(fill_base);
    lane = xs_scalar_misalign_skid(lane, (env->seed & 0x3u) + round);
    xs_scalar_misalign_write64(target_ptr_a, kTargetValue);
    xs_scalar_misalign_probe_high_fragment(fragment_base_a, &probe_word32, &probe_half16, &probe_byte8);
    lane = xs_scalar_misalign_skid(lane, ((env->seed >> 2) & 0x7u) + (round & 0x1u));
    xs_scalar_misalign_write64(target_ptr_b, kBlockerValue);
    lane = xs_scalar_misalign_skid(lane, ((env->seed >> 5) & 0x3u) + 1u);
    xs_scalar_misalign_probe_high_fragment(fragment_base_a, &probe_word32, &probe_half16, &probe_byte8);

    if (probe_word32 != kExpectedWord32 || probe_half16 != kExpectedHalf16 || probe_byte8 != kExpectedByte8) {
      env->snippet_id = ((uint64_t) probe_word32 << 32) | (uint64_t) probe_half16;
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 341u);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE0, probe_word32);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE1, probe_half16);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE2, probe_byte8);
      return XS_SCALAR_MISALIGN_RC_STORE_FORWARD_SEARCH;
    }
  }

  env->snippet_id = XS_SCALAR_MISALIGN_STORE_FORWARD_SEARCH_MAGIC ^ (uint64_t) repeat_count;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_SEARCH_COMPLETED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, repeat_count);
  return 0;
}

const xsrt_snippet_desc_t snippet_store_forward_search = {
  .id = "store_forward_search",
  .run = store_forward_search_run,
};
