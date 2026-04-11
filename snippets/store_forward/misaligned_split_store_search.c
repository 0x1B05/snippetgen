#include <stdint.h>

#include "xs_snippet.h"
#include "xs_split_store_forward.h"
#include "xsrt_csr.h"


static uint8_t split_store_arena[32768] __attribute__((aligned(64)));


static unsigned long split_store_skid(unsigned long lane, unsigned long count) {
  for (unsigned long index = 0; index < count; ++index) {
#if defined(__riscv)
    __asm__ volatile(
        "addi %[lane], %[lane], 3\n"
        "xori %[lane], %[lane], 11\n"
        "andi %[lane], %[lane], 255\n"
        : [lane] "+r"(lane)
        :
        : "memory");
#else
    lane = ((lane + 3u) ^ 11u) & 255u;
#endif
  }

  return lane;
}


static void split_store_write64(uint8_t *ptr, uint64_t value) {
#if defined(__riscv)
  __asm__ volatile(
      "sd %0, 0(%1)"
      :
      : "r"(value), "r"(ptr)
      : "memory");
#else
  for (unsigned long index = 0; index < 8u; ++index) {
    ptr[index] = (uint8_t) (value >> (8u * index));
  }
#endif
}


static void split_store_fill_burst(uint8_t *fill_base) {
  static const uint64_t kFillValue = 0x13579bdf2468ace0ull;

  split_store_write64(fill_base + 0u, kFillValue);
  split_store_write64(fill_base + 64u, kFillValue);
  split_store_write64(fill_base + 128u, kFillValue);
  split_store_write64(fill_base + 192u, kFillValue);
  split_store_write64(fill_base + 256u, kFillValue);
  split_store_write64(fill_base + 320u, kFillValue);
  split_store_write64(fill_base + 384u, kFillValue);
  split_store_write64(fill_base + 448u, kFillValue);
  split_store_write64(fill_base + 512u, kFillValue);
  split_store_write64(fill_base + 576u, kFillValue);
  split_store_write64(fill_base + 640u, kFillValue);
  split_store_write64(fill_base + 704u, kFillValue);
  split_store_write64(fill_base + 768u, kFillValue);
  split_store_write64(fill_base + 832u, kFillValue);
  split_store_write64(fill_base + 896u, kFillValue);
  split_store_write64(fill_base + 960u, kFillValue);
}


static void split_store_probe_high_fragment(
    uint8_t *fragment_base,
    uint32_t *word32,
    uint16_t *half16,
    uint8_t *byte8) {
#if defined(__riscv)
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
#else
  *word32 = *(uint32_t *) fragment_base;
  *half16 = *(uint16_t *) (fragment_base + 4u);
  *byte8 = *(uint8_t *) (fragment_base + 6u);
#endif
}


static void split_store_zero_target_region(uint8_t *low_word_base, uint8_t *high_word_base) {
  *(uint64_t *) low_word_base = 0u;
  *(uint64_t *) high_word_base = 0u;
}


static int misaligned_split_store_search_run(xsrt_env_t *env) {
  static const uint64_t kTargetValue = 0x8877665544332211ull;
  static const uint64_t kBlockerValue = 0x00ffeeddccbbaa99ull;
  static const uint32_t kExpectedWord32 = 0x55443322u;
  static const uint16_t kExpectedHalf16 = 0x7766u;
  static const uint8_t kExpectedByte8 = 0x88u;
  unsigned long lane;
  unsigned long repeat_count;
  unsigned long pre_pad;
  unsigned long between_targets_pad;
  unsigned long post_b_pad;
  unsigned long inter_probe_pad;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SPLIT_STORE_FLAG_ENTERED;
  lane = (unsigned long) (env->seed | 1u);
  repeat_count = 2u + (unsigned long) ((env->seed >> 16) & 0x7u);
  pre_pad = (unsigned long) (env->seed & 0x3u);
  between_targets_pad = (unsigned long) ((env->seed >> 2) & 0x7u);
  inter_probe_pad = (unsigned long) ((env->seed >> 5) & 0x3u);
  post_b_pad = (unsigned long) ((env->seed >> 7) & 0x3u);

  for (unsigned long round = 0; round < repeat_count; ++round) {
    uint8_t *slot_base;
    uint8_t *target_base_a;
    uint8_t *fragment_base_a;
    uint8_t *target_ptr_a;
    uint8_t *target_base_b;
    uint8_t *fragment_base_b;
    uint8_t *target_ptr_b;
    uint8_t *fill_base;
    uint32_t probe0_word32;
    uint16_t probe0_half16;
    uint8_t probe0_byte8;
    uint32_t probe1_word32;
    uint16_t probe1_half16;
    uint8_t probe1_byte8;
    uint32_t probe2_word32;
    uint16_t probe2_half16;
    uint8_t probe2_byte8;
    uint32_t probe3_word32;
    uint16_t probe3_half16;
    uint8_t probe3_byte8;

    slot_base = &split_store_arena[4096u * ((round + (unsigned long) (env->seed >> 24)) & 0x7u)];
    target_base_a = slot_base;
    fragment_base_a = target_base_a + 64u;
    target_ptr_a = fragment_base_a - 1u;
    target_base_b = slot_base + 2048u;
    fragment_base_b = target_base_b + 64u;
    target_ptr_b = fragment_base_b - 1u;
    fill_base = target_base_a + 128u;

    split_store_zero_target_region(target_base_a + 56u, fragment_base_a);
    split_store_zero_target_region(target_base_b + 56u, fragment_base_b);
    split_store_fill_burst(fill_base);
    lane = split_store_skid(lane, pre_pad + (round & 0x1u));
    split_store_write64(target_ptr_a, kTargetValue);
    split_store_probe_high_fragment(fragment_base_a, &probe0_word32, &probe0_half16, &probe0_byte8);
    lane = split_store_skid(lane, inter_probe_pad + (round & 0x1u));
    split_store_probe_high_fragment(fragment_base_a, &probe1_word32, &probe1_half16, &probe1_byte8);
    lane = split_store_skid(lane, between_targets_pad + ((round >> 1) & 0x1u));
    split_store_write64(target_ptr_b, kBlockerValue);
    lane = split_store_skid(lane, post_b_pad + (round & 0x1u));
    split_store_probe_high_fragment(fragment_base_a, &probe2_word32, &probe2_half16, &probe2_byte8);
    lane = split_store_skid(lane, inter_probe_pad + ((round >> 1) & 0x1u));
    split_store_probe_high_fragment(fragment_base_a, &probe3_word32, &probe3_half16, &probe3_byte8);

    if (probe0_word32 != kExpectedWord32 || probe0_half16 != kExpectedHalf16 || probe0_byte8 != kExpectedByte8 ||
        probe1_word32 != kExpectedWord32 || probe1_half16 != kExpectedHalf16 || probe1_byte8 != kExpectedByte8 ||
        probe2_word32 != kExpectedWord32 || probe2_half16 != kExpectedHalf16 || probe2_byte8 != kExpectedByte8 ||
        probe3_word32 != kExpectedWord32 || probe3_half16 != kExpectedHalf16 || probe3_byte8 != kExpectedByte8) {
      env->snippet_id = ((uint64_t) probe0_word32 << 32) | (uint64_t) probe2_word32;
      xsrt_csr_write(8u, kTargetValue);
      xsrt_csr_write(9u, ((uint64_t) probe0_word32 << 32) | (uint64_t) probe0_half16 << 8 | (uint64_t) probe0_byte8);
      xsrt_csr_write(10u, (uint64_t) (uintptr_t) target_ptr_a);
      xsrt_csr_write(11u, round);
      xsrt_csr_write(12u, probe0_word32);
      xsrt_csr_write(13u, probe0_half16);
      xsrt_csr_write(14u, probe0_byte8);
      xsrt_csr_write(15u, probe1_word32);
      xsrt_csr_write(16u, probe1_half16);
      xsrt_csr_write(17u, probe1_byte8);
      xsrt_csr_write(18u, (uint64_t) (uintptr_t) target_ptr_b);
      xsrt_csr_write(19u, probe2_word32);
      xsrt_csr_write(20u, probe2_half16);
      xsrt_csr_write(21u, probe2_byte8);
      xsrt_csr_write(22u, probe3_word32);
      xsrt_csr_write(23u, probe3_half16);
      xsrt_csr_write(24u, probe3_byte8);
      return XS_SPLIT_STORE_RC_MISMATCH;
    }
  }

  env->snippet_id = XS_SPLIT_STORE_SNIPPET_MAGIC ^ (uint64_t) repeat_count;
  xsrt_csr_write(8u, repeat_count);
  env->flags |= (uint64_t) XS_SPLIT_STORE_FLAG_COMPLETED;
  return 0;
}


const xsrt_snippet_desc_t snippet_misaligned_split_store_search = {
  .id = "misaligned_split_store_search",
  .run = misaligned_split_store_search_run,
};
