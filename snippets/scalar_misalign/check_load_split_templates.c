#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

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

  if (
      xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_LOAD_SPLIT_SUMMARY) !=
      (((uint64_t) XS_SCALAR_MISALIGN_LOAD_SPLIT_MAGIC << 32) | 6u)) {
    return 403;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_load_split_templates = {
  .id = "check_load_split_templates",
  .check = check_load_split_templates_check,
};
