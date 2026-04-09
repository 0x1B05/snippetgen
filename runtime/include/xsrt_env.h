#ifndef XSRT_ENV_H
#define XSRT_ENV_H

#include <stdint.h>

typedef struct {
  uint64_t hartid;
  uint64_t test_id;
  uint64_t snippet_id;
  uint64_t seed;
  uint64_t flags;
} xsrt_env_t;

enum {
  XSRT_FLAG_FINISHED = 1u << 0,
  XSRT_FLAG_FAILED = 1u << 1,
};

void xsrt_init(xsrt_env_t *env);
void xsrt_finish_pass(xsrt_env_t *env);
void xsrt_finish_fail(xsrt_env_t *env, uint64_t code);

#endif
