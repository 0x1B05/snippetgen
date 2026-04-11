#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"


static int check_interrupt_response_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_INTERRUPT_FLAG_TIMER_ARMED) == 0u) {
    return 81;
  }

  if ((env->flags & (uint64_t) XS_INTERRUPT_FLAG_TRAP_OBSERVED) == 0u) {
    return 82;
  }

  if (env->interrupt_count == 0u) {
    return 83;
  }

  if (env->last_trap_cause != XS_INTERRUPT_MCAUSE_MTIP) {
    return 84;
  }

  if (env->last_trap_epc == 0u) {
    return 85;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_interrupt_response = {
  .id = "check_interrupt_response",
  .check = check_interrupt_response_check,
};
