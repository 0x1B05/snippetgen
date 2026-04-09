#include "xsrt_env.h"

#include <stddef.h>
#include <string.h>

#include "xsrt_platform.h"

void xsrt_init(xsrt_env_t *env) {
  if (env == NULL) {
    return;
  }

  memset(env, 0, sizeof(*env));
  xsrt_platform_init(env);
}

void xsrt_finish_pass(xsrt_env_t *env) {
  if (env == NULL) {
    return;
  }

  env->flags |= XSRT_FLAG_FINISHED;
  env->flags &= ~((uint64_t) XSRT_FLAG_FAILED);
  xsrt_platform_finish(env, 0);
}

void xsrt_finish_fail(xsrt_env_t *env, uint64_t code) {
  if (env == NULL) {
    return;
  }

  env->flags |= XSRT_FLAG_FINISHED | XSRT_FLAG_FAILED;
  xsrt_platform_finish(env, code);
}
