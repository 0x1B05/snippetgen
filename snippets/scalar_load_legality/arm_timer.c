#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"
#include "xsrt_intr.h"


static int arm_timer_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  xsrt_enable_stimer();
  xsrt_timer_arm_delta(64u);
  env->flags |= (uint64_t) XS_INTERRUPT_FLAG_TIMER_ARMED;
  return 0;
}


const xsrt_snippet_desc_t snippet_arm_timer = {
  .id = "arm_timer",
  .run = arm_timer_run,
};
