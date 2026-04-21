#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint64_t xs_scalar_misalign_expected_cross_summary(uint64_t seed) {
  const unsigned rounds = 2u + (unsigned) ((seed >> 2) & 0x3u);
  const unsigned load_seed = (unsigned) (seed & 0x3u);
  const unsigned store_seed = (unsigned) ((seed >> 4) & 0x3u);

  return ((uint64_t) XS_SCALAR_MISALIGN_CROSS_PAGE_MAGIC << 32) |
      ((uint64_t) store_seed << 16) |
      ((uint64_t) load_seed << 8) |
      (uint64_t) rounds;
}

static int check_cross_page_faults_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_ENTERED) == 0u) {
    return 421;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_COMPLETED) == 0u) {
    return 422;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_CROSS_CAUSE0) != XS_SCALAR_MISALIGN_LOAD_PAGE_CAUSE) {
    return 423;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_CROSS_CAUSE1) != XS_SCALAR_MISALIGN_STORE_ACCESS_CAUSE) {
    return 424;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_CROSS_SUMMARY) !=
      xs_scalar_misalign_expected_cross_summary(env->seed)) {
    return 425;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_cross_page_faults = {
  .id = "check_cross_page_faults",
  .check = check_cross_page_faults_check,
};
