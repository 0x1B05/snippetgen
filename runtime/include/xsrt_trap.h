#ifndef XSRT_TRAP_H
#define XSRT_TRAP_H

#include <stdint.h>

typedef struct xsrt_trap_frame xsrt_trap_frame_t;

struct xsrt_trap_frame {
  uint64_t epc;
  uint64_t cause;
  uint64_t tval;
  uint64_t gpr[32];
};

typedef xsrt_trap_frame_t *(*xsrt_trap_handler_t)(xsrt_trap_frame_t *);

void xsrt_install_strap(xsrt_trap_handler_t fn);

#endif
