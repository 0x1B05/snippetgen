#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"
#include "xs_vsetvl_interrupt_path.h"


static int check_vsetvl_interrupt_path_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_INTERRUPT_FLAG_TIMER_ARMED) == 0u) {
    return 61;
  }

  if ((env->flags & (uint64_t) XS_VSETVL_FLAG_ENTERED) == 0u) {
    return 62;
  }

  if ((env->flags & (uint64_t) XS_VSETVL_FLAG_COMPLETED) == 0u) {
    return 63;
  }

  if (env->snippet_id != XS_VSETVL_SNIPPET_MAGIC) {
    return 64;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_vsetvl_interrupt_path = {
  .id = "check_vsetvl_interrupt_path",
  .check = check_vsetvl_interrupt_path_check,
};
