#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

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

static uint64_t xs_scalar_misalign_expected_forward_summary(uint64_t seed) {
  return ((uint64_t) XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC << 32) |
      ((uint64_t) xs_scalar_misalign_forward_between_stride(seed) << 24) |
      ((uint64_t) xs_scalar_misalign_forward_pre_stride(seed) << 16) |
      ((uint64_t) xs_scalar_misalign_forward_pair_seed(seed) << 8) |
      (uint64_t) xs_scalar_misalign_forward_rounds(seed);
}

static uint64_t xs_scalar_misalign_expected_target_value(uint64_t seed) {
  const unsigned round = xs_scalar_misalign_forward_rounds(seed) - 1u;
  uint64_t value = 0x8877665544332211ull;

  value ^= ((uint64_t) (seed & 0xffu)) << 8;
  value ^= ((uint64_t) ((seed >> 8) & 0xffu)) << 24;
  value ^= (uint64_t) round << 40;
  return value;
}

static int check_store_forward_overlap_check(xsrt_env_t *env) {
  const uint64_t expected_value = xs_scalar_misalign_expected_target_value(env != 0 ? env->seed : 0u);

  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_ENTERED) == 0u) {
    return 431;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_COMPLETED) == 0u) {
    return 432;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0) != expected_value) {
    return 433;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1) != expected_value) {
    return 434;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY) !=
      xs_scalar_misalign_expected_forward_summary(env->seed)) {
    return 435;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_store_forward_overlap = {
  .id = "check_store_forward_overlap",
  .check = check_store_forward_overlap_check,
};
