#include "xsrt_platform.h"

static uint64_t g_last_finish_code;

void xsrt_platform_init(xsrt_env_t *env) {
  (void) env;
  g_last_finish_code = 0;
}

void xsrt_platform_finish(xsrt_env_t *env, uint64_t code) {
  (void) env;
  g_last_finish_code = code;
}

uint64_t xsrt_platform_last_finish_code(void) {
  return g_last_finish_code;
}
