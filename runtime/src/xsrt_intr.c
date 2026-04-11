#include "xsrt_intr.h"

#include "xsrt_env.h"

static int g_stimer_enabled;
static uint64_t g_timer_delta;

#if defined(__riscv)
extern void xsrt_trap_entry(void);
#endif

typedef struct {
  uint64_t mtimecmp_addr;
  uint64_t delta;
  uint64_t env_ptr;
  uint64_t scratch_a1;
  uint64_t scratch_a2;
  uint64_t scratch_a3;
} xsrt_timer_state_t;

enum {
  XSRT_MSTATUS_MIE = 1u << 3,
  XSRT_MIE_MTIE = 1u << 7,
};

#define XSRT_CLINT_MTIMECMP_ADDR 0x38004000ull
#define XSRT_RTC_ADDR ((volatile uint64_t *) 0x3800bff8ull)
#define XSRT_CLINT_MTIMECMP ((volatile uint64_t *) 0x38004000ull)

static xsrt_timer_state_t g_timer_state = {
    .mtimecmp_addr = XSRT_CLINT_MTIMECMP_ADDR,
};

void xsrt_enable_stimer(void) {
  g_stimer_enabled = 1;
  g_timer_state.env_ptr = (uint64_t) (uintptr_t) xsrt_current_env();
#if defined(__riscv)
  {
    const unsigned long mie_mask = XSRT_MIE_MTIE;
    const unsigned long mstatus_mask = XSRT_MSTATUS_MIE;
    __asm__ volatile("csrw mscratch, %0" : : "r"(&g_timer_state) : "memory");
    __asm__ volatile("csrw mtvec, %0" : : "r"(&xsrt_trap_entry) : "memory");
    __asm__ volatile("csrs mie, %0" : : "r"(mie_mask) : "memory");
    __asm__ volatile("csrs mstatus, %0" : : "r"(mstatus_mask) : "memory");
  }
#endif
}

void xsrt_disable_stimer(void) {
  g_stimer_enabled = 0;
#if defined(__riscv)
  {
    const unsigned long mie_mask = XSRT_MIE_MTIE;
    __asm__ volatile("csrc mie, %0" : : "r"(mie_mask) : "memory");
  }
#endif
}

void xsrt_timer_arm_delta(uint64_t cycles) {
  if (g_stimer_enabled == 0) {
    return;
  }

  g_timer_delta = cycles;
  g_timer_state.delta = cycles;
  g_timer_state.env_ptr = (uint64_t) (uintptr_t) xsrt_current_env();
#if defined(__riscv)
  *XSRT_CLINT_MTIMECMP = *XSRT_RTC_ADDR + cycles;
#endif
}

uint64_t xsrt_timer_last_delta(void) {
  return g_timer_delta;
}
