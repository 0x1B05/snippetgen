#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"

enum {
  XS_INTERRUPT_WAIT_SPINS = 1024u,
  XS_INTERRUPT_WAIT_TIMEOUT = 71,
  XS_INTERRUPT_WAIT_PENDING_ONLY = 72,
  XS_INTERRUPT_WAIT_MSTATUS_DISABLED = 73,
  XS_INTERRUPT_WAIT_MIE_DISABLED = 74,
  XS_INTERRUPT_WAIT_TIMER_NOT_EXPIRED = 75,
  XS_INTERRUPT_MSTATUS_MIE = 1u << 3,
  XS_INTERRUPT_MIE_MTIE = 1u << 7,
  XS_INTERRUPT_MIP_MTIP = 1u << 7,
};

#define XS_INTERRUPT_RTC_ADDR ((volatile uint64_t *) 0x3800bff8ull)
#define XS_INTERRUPT_MTIMECMP_ADDR ((volatile uint64_t *) 0x38004000ull)


static int interrupt_response_wait_run(xsrt_env_t *env) {
  volatile xsrt_env_t *shared_env;
  uint64_t last_mstatus;
  uint64_t last_mie;
  uint64_t last_mip;
  uint64_t last_time;
  uint64_t last_compare;

  if (env == 0) {
    return -1;
  }

  shared_env = env;
  last_mstatus = 0u;
  last_mie = 0u;
  last_mip = 0u;
  last_time = 0u;
  last_compare = 0u;

  for (uint64_t spin = 0; spin < XS_INTERRUPT_WAIT_SPINS; ++spin) {
    if (shared_env->interrupt_count != 0u) {
      env->flags |= (uint64_t) XS_INTERRUPT_FLAG_TRAP_OBSERVED;
      return 0;
    }
#if defined(__riscv)
    __asm__ volatile("csrr %0, mstatus" : "=r"(last_mstatus));
    __asm__ volatile("csrr %0, mie" : "=r"(last_mie));
    __asm__ volatile("csrr %0, mip" : "=r"(last_mip));
    last_time = *XS_INTERRUPT_RTC_ADDR;
    last_compare = *XS_INTERRUPT_MTIMECMP_ADDR;
    __asm__ volatile("nop" ::: "memory");
#else
    __asm__ volatile("" ::: "memory");
#endif
  }

  if ((last_mstatus & (uint64_t) XS_INTERRUPT_MSTATUS_MIE) == 0u) {
    return XS_INTERRUPT_WAIT_MSTATUS_DISABLED;
  }

  if ((last_mie & (uint64_t) XS_INTERRUPT_MIE_MTIE) == 0u) {
    return XS_INTERRUPT_WAIT_MIE_DISABLED;
  }

  if (last_time < last_compare) {
    return XS_INTERRUPT_WAIT_TIMER_NOT_EXPIRED;
  }

  if ((last_mip & (uint64_t) XS_INTERRUPT_MIP_MTIP) != 0u) {
    return XS_INTERRUPT_WAIT_PENDING_ONLY;
  }

  return XS_INTERRUPT_WAIT_TIMEOUT;
}


const xsrt_snippet_desc_t snippet_interrupt_response_wait = {
  .id = "interrupt_response_wait",
  .run = interrupt_response_wait_run,
};
