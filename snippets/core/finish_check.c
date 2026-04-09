#include <stdint.h>

#include "xs_snippet.h"


static int finish_check_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & XSRT_FLAG_FAILED) != 0u) {
    return 31;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_finish_check = {
  .id = "finish_check",
  .check = finish_check_check,
};
