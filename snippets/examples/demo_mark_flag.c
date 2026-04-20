#include <stdint.h>

#include "xs_snippet.h"

enum {
  XS_DEMO_MARK_FLAG = 1u << 8,
};

static int demo_mark_flag_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_DEMO_MARK_FLAG;
  return 0;
}

const xsrt_snippet_desc_t snippet_demo_mark_flag = {
  .id = "demo_mark_flag",
  .run = demo_mark_flag_run,
};
