#include <stdint.h>

#include "xs_snippet.h"
#include "xs_interrupt_response.h"
#include "xs_vsetvl_interrupt_path.h"
#include "xsrt_intr.h"


static unsigned long vsetvl_search_skid(unsigned long lane, unsigned long count) {
  for (unsigned long index = 0; index < count; ++index) {
#if defined(__riscv)
    __asm__ volatile(
        "addi %[lane], %[lane], 1\n"
        "xori %[lane], %[lane], 7\n"
        "andi %[lane], %[lane], 255\n"
        : [lane] "+r"(lane)
        :
        : "memory");
#else
    lane = ((lane + 1u) ^ 7u) & 255u;
#endif
  }

  return lane;
}


static int vsetvl_interrupt_search_run(xsrt_env_t *env) {
  unsigned long iterations;
  unsigned long pre_pad;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) (XS_INTERRUPT_FLAG_TIMER_ARMED | XS_VSETVL_FLAG_ENTERED);

  iterations = 512u + (unsigned long) ((env->seed >> 4) & 0x1ffu);
  pre_pad = (unsigned long) (env->seed & 0x7u);

#if defined(__riscv)
  {
    const unsigned long vs_mask = XS_VSETVL_MSTATUS_VS_MASK;
    __asm__ volatile("csrs mstatus, %0" : : "r"(vs_mask) : "memory");
  }
#endif

  xsrt_enable_stimer();
  xsrt_timer_arm_delta(16u + (uint64_t) ((env->seed >> 13) & 0xfu));
  (void) vsetvl_search_skid((unsigned long) env->seed, pre_pad);

  for (unsigned long index = 0; index < iterations; ++index) {
#if defined(__riscv)
    __asm__ volatile(
        ".option push\n"
        ".option arch, +v\n"
        "vsetvl zero, zero, zero\n"
        ".option pop\n"
        :
        :
        : "memory");
#else
    __asm__ volatile("" ::: "memory");
#endif
  }

  env->snippet_id = XS_VSETVL_SNIPPET_MAGIC ^ (uint64_t) iterations;
  env->flags |= (uint64_t) XS_VSETVL_FLAG_COMPLETED;
  return 0;
}


const xsrt_snippet_desc_t snippet_vsetvl_interrupt_search = {
  .id = "vsetvl_interrupt_search",
  .run = vsetvl_interrupt_search_run,
};
