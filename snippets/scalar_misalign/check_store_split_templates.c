#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

enum {
  XS_SCALAR_MISALIGN_STORE_CASE_COUNT = 6u,
};

static uint64_t xs_scalar_misalign_expected_store_summary(uint64_t seed) {
  const unsigned rounds = 2u + (unsigned) ((seed >> 12) & 0x3u);
  const unsigned rotation = (unsigned) (((seed >> 7) ^ seed) % XS_SCALAR_MISALIGN_STORE_CASE_COUNT);
  const unsigned bank_seed = (unsigned) ((seed >> 10) & 0x7u);
  const unsigned total_cases = rounds * XS_SCALAR_MISALIGN_STORE_CASE_COUNT;

  return ((uint64_t) XS_SCALAR_MISALIGN_STORE_SPLIT_MAGIC << 32) |
      ((uint64_t) rounds << 24) |
      ((uint64_t) bank_seed << 16) |
      ((uint64_t) rotation << 8) |
      (uint64_t) total_cases;
}

static int check_store_split_templates_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_ENTERED) == 0u) {
    return 411;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_SPLIT_COMPLETED) == 0u) {
    return 412;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_STORE_SPLIT_SUMMARY) !=
      xs_scalar_misalign_expected_store_summary(env->seed)) {
    return 413;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_store_split_templates = {
  .id = "check_store_split_templates",
  .check = check_store_split_templates_check,
};
