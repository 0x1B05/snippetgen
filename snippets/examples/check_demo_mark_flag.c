#include <stdint.h>

#include "xs_snippet.h"

enum {
  XS_DEMO_MARK_FLAG = 1u << 8,
  XS_DEMO_MARK_FLAG_MISSING = 91,
};

static int check_demo_mark_flag_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_DEMO_MARK_FLAG) == 0u) {
    return XS_DEMO_MARK_FLAG_MISSING;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_demo_mark_flag = {
  .id = "check_demo_mark_flag",
  .check = check_demo_mark_flag_check,
};
