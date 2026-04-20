#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_forward_arena[256] __attribute__((aligned(64)));

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

static int store_forward_overlap_run(xsrt_env_t *env) {
  static const uint64_t kTargetValue = 0x8877665544332211ull;
  static const uint64_t kBlockerValue = 0x1020304050607080ull;
  uint8_t *slot_a = &xs_scalar_misalign_forward_arena[0];
  uint8_t *slot_b = &xs_scalar_misalign_forward_arena[128];
  uint8_t *store_ptr = slot_a + 63u;
  uint8_t *fragment_ptr = slot_a + 64u;
  uint8_t *blocker_ptr = slot_b + 63u;
  uint64_t value0;
  uint64_t value1;
  uint32_t high_word;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY, 0u);

  xs_scalar_misalign_zero_region(xs_scalar_misalign_forward_arena, sizeof(xs_scalar_misalign_forward_arena));

  xs_scalar_misalign_sd(store_ptr, kTargetValue);
  value0 = xs_scalar_misalign_ld(store_ptr);
  high_word = xs_scalar_misalign_lwu(fragment_ptr);
  xs_scalar_misalign_sd(blocker_ptr, kBlockerValue);
  value1 = xs_scalar_misalign_ld(store_ptr);

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0, value0);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1, value1);

  if (value0 != kTargetValue) {
    xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 331u);
    return XS_SCALAR_MISALIGN_RC_STORE_FORWARD;
  }

  if (high_word != 0x55443322u) {
    xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 332u);
    return XS_SCALAR_MISALIGN_RC_STORE_FORWARD + 1;
  }

  if (value1 != kTargetValue) {
    xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 333u);
    return XS_SCALAR_MISALIGN_RC_STORE_FORWARD + 2;
  }

  xsrt_csr_write(
      XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY,
      ((uint64_t) XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC << 32) | 2u);
  env->snippet_id = XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC ^ 2u;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_COMPLETED;
  return 0;
}

const xsrt_snippet_desc_t snippet_store_forward_overlap = {
  .id = "store_forward_overlap",
  .run = store_forward_overlap_run,
};
