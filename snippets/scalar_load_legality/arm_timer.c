#include <stdint.h>

#include "xs_snippet.h"
#include "xsrt_intr.h"
#include "xsrt_trap.h"


static int arm_timer_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  xsrt_install_strap(0);
  xsrt_enable_stimer();
  xsrt_timer_arm_delta(64u);
  env->flags |= (uint64_t) 0x10u;
  return 0;
}


const xsrt_snippet_desc_t snippet_arm_timer = {
  .id = "arm_timer",
  .run = arm_timer_run,
};
