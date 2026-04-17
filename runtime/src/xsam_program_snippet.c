#include "xsam/program_snippet.h"

static xsrt_env_t *g_program_env;

static int xsam_call_program_main(xsam_program_main_t entry) {
  return entry();
}

xsrt_env_t *xsam_current_env(void) {
  return g_program_env;
}

int xsam_run_program_main(xsrt_env_t *env, xsam_program_main_t entry) {
  xsrt_env_t *prev_env;
  int rc;

  if (env == 0 || entry == 0) {
    return -1;
  }

  prev_env = g_program_env;
  g_program_env = env;
  rc = xsam_call_program_main(entry);
  g_program_env = prev_env;
  return rc;
}
