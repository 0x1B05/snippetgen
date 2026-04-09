#ifndef XSRT_INTR_H
#define XSRT_INTR_H

#include <stdint.h>

void xsrt_enable_stimer(void);
void xsrt_timer_arm_delta(uint64_t cycles);

#endif
