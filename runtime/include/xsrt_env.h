#ifndef XSRT_ENV_H
#define XSRT_ENV_H

#include <stdint.h>

typedef struct {
  uint64_t hartid;
  uint64_t test_id;
  uint64_t snippet_id;
  uint64_t seed;
  uint64_t flags;
  uint64_t interrupt_count;
  uint64_t last_trap_cause;
  uint64_t last_trap_epc;
} xsrt_env_t;

enum {
  XSRT_FLAG_FINISHED = 1u << 0,
  XSRT_FLAG_FAILED = 1u << 1,
};

#define XSRT_BAD_TRAP(code)                                                     \
  do {                                                                          \
    __asm__ volatile(                                                           \
        "mv a0, %0\n\t"                                                         \
        ".word 0x0005006b\n\t"                                                  \
        :                                                                       \
        : "r"((uint64_t) (code))                                                \
        : "a0", "memory");                                                      \
    __builtin_unreachable();                                                    \
  } while (0)

void xsrt_init(xsrt_env_t *env);
void xsrt_finish_pass(xsrt_env_t *env);
void xsrt_finish_fail(xsrt_env_t *env, uint64_t code);
xsrt_env_t *xsrt_current_env(void);

#endif
