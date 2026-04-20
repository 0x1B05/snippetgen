#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static int check_cross_page_fault_search_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_SEARCH_ENTERED) == 0u) {
    return 451;
  }

  if ((env->flags & (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_SEARCH_COMPLETED) == 0u) {
    return 452;
  }

  if (xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT) == 0u) {
    return 453;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_cross_page_fault_search = {
  .id = "check_cross_page_fault_search",
  .check = check_cross_page_fault_search_check,
};
