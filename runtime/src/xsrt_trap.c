#include "xsrt_trap.h"

static xsrt_trap_handler_t g_s_trap_handler;

#if defined(__riscv)
extern void xsrt_trap_entry(void);
#endif

void xsrt_install_strap(xsrt_trap_handler_t fn) {
  g_s_trap_handler = fn;
#if defined(__riscv)
  __asm__ volatile("csrw mtvec, %0" : : "r"(&xsrt_trap_entry) : "memory");
#endif
}

xsrt_trap_frame_t *xsrt_dispatch_strap(xsrt_trap_frame_t *frame) {
  if (g_s_trap_handler == 0) {
    return frame;
  }

  return g_s_trap_handler(frame);
}
