#include <stdint.h>

#include "xs_snippet.h"
#include "xs_split_store_forward.h"
#include "xsrt_csr.h"


static int check_misaligned_split_store_search_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_SPLIT_STORE_FLAG_ENTERED) == 0u) {
    return 111;
  }

  if ((env->flags & (uint64_t) XS_SPLIT_STORE_FLAG_COMPLETED) == 0u) {
    return 112;
  }

  if (xsrt_csr_read(8u) == 0u) {
    return 113;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_misaligned_split_store_search = {
  .id = "check_misaligned_split_store_search",
  .check = check_misaligned_split_store_search_check,
};
