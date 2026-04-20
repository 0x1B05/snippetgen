#include <stdint.h>

#include "xs_snippet.h"

enum {
  XS_DEFERRED_STAGE_A_RUN = 1ull << 8,
  XS_DEFERRED_STAGE_A_FINI = 1ull << 9,
  XS_DEFERRED_STAGE_B_RUN = 1ull << 10,
  XS_DEFERRED_STAGE_B_FINI = 1ull << 11,
};

static int deferred_mark_stage_a_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_DEFERRED_STAGE_A_RUN;
  env->snippet_id = 0xa1u;
  return 0;
}

static int deferred_mark_stage_a_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_A_RUN) == 0u) {
    return 501;
  }

  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_B_RUN) == 0u) {
    return 502;
  }

  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_B_FINI) == 0u) {
    return 503;
  }

  return 0;
}

static void deferred_mark_stage_a_fini(xsrt_env_t *env) {
  if (env != 0) {
    env->flags |= (uint64_t) XS_DEFERRED_STAGE_A_FINI;
  }
}

const xsrt_snippet_desc_t snippet_deferred_mark_stage_a = {
  .id = "deferred_mark_stage_a",
  .run = deferred_mark_stage_a_run,
  .check = deferred_mark_stage_a_check,
  .fini = deferred_mark_stage_a_fini,
};
