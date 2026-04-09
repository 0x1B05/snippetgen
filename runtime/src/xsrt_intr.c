#include "xsrt_intr.h"

static int g_stimer_enabled;
static uint64_t g_timer_delta;

void xsrt_enable_stimer(void) {
  g_stimer_enabled = 1;
}

void xsrt_timer_arm_delta(uint64_t cycles) {
  if (g_stimer_enabled == 0) {
    return;
  }

  g_timer_delta = cycles;
}

uint64_t xsrt_timer_last_delta(void) {
  return g_timer_delta;
}
