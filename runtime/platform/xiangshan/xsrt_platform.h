#ifndef XSRT_PLATFORM_H
#define XSRT_PLATFORM_H

#include <stdint.h>

#include "xsrt_env.h"

void xsrt_platform_init(xsrt_env_t *env);
void xsrt_platform_finish(xsrt_env_t *env, uint64_t code);
uint64_t xsrt_platform_last_finish_code(void);

#endif
