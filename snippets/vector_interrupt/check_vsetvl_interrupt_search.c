#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"
#include "xs_vsetvl_interrupt_path.h"


static int check_vsetvl_interrupt_search_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_INTERRUPT_FLAG_TIMER_ARMED) == 0u) {
    return 91;
  }

  if ((env->flags & (uint64_t) XS_VSETVL_FLAG_ENTERED) == 0u) {
    return 92;
  }

  if ((env->flags & (uint64_t) XS_VSETVL_FLAG_COMPLETED) == 0u) {
    return 93;
  }

  if (env->interrupt_count == 0u) {
    return 94;
  }

  if (env->last_trap_cause != XS_INTERRUPT_MCAUSE_MTIP) {
    return 95;
  }

  if (env->last_trap_epc == 0u) {
    return 96;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_vsetvl_interrupt_search = {
  .id = "check_vsetvl_interrupt_search",
  .check = check_vsetvl_interrupt_search_check,
};
