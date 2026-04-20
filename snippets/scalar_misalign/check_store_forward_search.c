#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static int check_store_forward_search_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_SEARCH_ENTERED) == 0u) {
    return 441;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_STORE_FORWARD_SEARCH_COMPLETED) == 0u) {
    return 442;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT) == 0u) {
    return 443;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_store_forward_search = {
  .id = "check_store_forward_search",
  .check = check_store_forward_search_check,
};
