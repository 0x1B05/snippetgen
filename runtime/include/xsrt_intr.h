#ifndef XSRT_INTR_H
#define XSRT_INTR_H

#include <stdint.h>

void xsrt_enable_stimer(void);
void xsrt_disable_stimer(void);
void xsrt_timer_arm_delta(uint64_t cycles);
void xsrt_timer_arm_periodic_delta(uint64_t cycles);
uint64_t xsrt_timer_last_delta(void);

#endif
