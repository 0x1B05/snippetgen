#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static int check_store_forward_overlap_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_ENTERED) == 0u) {
    return 431;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_COMPLETED) == 0u) {
    return 432;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE0) != 0x8877665544332211ull) {
    return 433;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_VALUE1) != 0x8877665544332211ull) {
    return 434;
  }

  if (
      xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY) !=
      (((uint64_t) XS_SCALAR_MISALIGN_STORE_FORWARD_MAGIC << 32) | 2u)) {
    return 435;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_store_forward_overlap = {
  .id = "check_store_forward_overlap",
  .check = check_store_forward_overlap_check,
};
