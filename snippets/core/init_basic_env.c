#include <stdint.h>

#include "xs_snippet.h"


static int init_basic_env_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  env->hartid = 0;
  env->test_id = 0x5347u;
  if (env->seed == 0) {
    env->seed = 0x1234u;
  }
  env->flags = 0;
  return 0;
}


const xsrt_snippet_desc_t snippet_init_basic_env = {
  .id = "init_basic_env",
  .run = init_basic_env_run,
};
