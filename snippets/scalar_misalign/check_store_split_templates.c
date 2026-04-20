#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

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

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT) != 6u) {
    return 413;
  }

  if ((env->snippet_id & 0xffff0000u) != (XS_SCALAR_MISALIGN_STORE_SPLIT_MAGIC & 0xffff0000u)) {
    return 414;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_store_split_templates = {
  .id = "check_store_split_templates",
  .check = check_store_split_templates_check,
};
