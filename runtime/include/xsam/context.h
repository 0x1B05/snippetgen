#ifndef XSAM_CONTEXT_H
#define XSAM_CONTEXT_H

#include <stdint.h>

struct xsam_context {
  uintptr_t gpr[32];
  uintptr_t cause;
  uintptr_t status;
  uintptr_t epc;
  void *pdir;
};

#endif
