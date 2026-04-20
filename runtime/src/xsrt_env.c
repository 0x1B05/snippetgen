#include "xsrt_env.h"

#include <stddef.h>

#include "xsrt_platform.h"

static xsrt_env_t *g_current_env;

void xsrt_init(xsrt_env_t *env) {
  uint64_t *words;
  unsigned long index;

  if (env == NULL) {
    return;
  }

  words = (uint64_t *) env;
  for (index = 0; index < sizeof(*env) / sizeof(uint64_t); ++index) {
    words[index] = 0;
  }
  g_current_env = env;
  xsrt_platform_init(env);
}

void xsrt_finish_pass(xsrt_env_t *env) {
  if (env == NULL) {
    return;
  }

  env->flags |= XSRT_FLAG_FINISHED;
  env->flags &= ~((uint64_t) XSRT_FLAG_FAILED);
  env->finish_code = 0u;
  xsrt_platform_finish(env, 0);
}

void xsrt_finish_fail(xsrt_env_t *env, uint64_t code) {
  if (env == NULL) {
    return;
  }

  env->flags |= XSRT_FLAG_FINISHED | XSRT_FLAG_FAILED;
  env->finish_code = code;
  xsrt_platform_finish(env, code);
}

xsrt_env_t *xsrt_current_env(void) {
  return g_current_env;
}
