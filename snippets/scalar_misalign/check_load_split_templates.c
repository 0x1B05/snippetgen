#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

enum {
  XS_SCALAR_MISALIGN_LOAD_CASE_COUNT = 6u,
};

static uint64_t xs_scalar_misalign_expected_load_summary(uint64_t seed) {
  const unsigned rounds = 2u + (unsigned) ((seed >> 5) & 0x3u);
  const unsigned rotation = (unsigned) ((seed ^ (seed >> 7)) % XS_SCALAR_MISALIGN_LOAD_CASE_COUNT);
  const unsigned bank_seed = (unsigned) ((seed >> 3) & 0x7u);
  const unsigned total_cases = rounds * XS_SCALAR_MISALIGN_LOAD_CASE_COUNT;

  return ((uint64_t) XS_SCALAR_MISALIGN_LOAD_SPLIT_MAGIC << 32) |
      ((uint64_t) rounds << 24) |
      ((uint64_t) bank_seed << 16) |
      ((uint64_t) rotation << 8) |
      (uint64_t) total_cases;
}

static int check_load_split_templates_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_ENTERED) == 0u) {
    return 401;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_LOAD_SPLIT_COMPLETED) == 0u) {
    return 402;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_LOAD_SPLIT_SUMMARY) !=
      xs_scalar_misalign_expected_load_summary(env->seed)) {
    return 403;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_load_split_templates = {
  .id = "check_load_split_templates",
  .check = check_load_split_templates_check,
};
