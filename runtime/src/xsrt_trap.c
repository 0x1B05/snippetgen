#include "xsrt_trap.h"

static xsrt_trap_handler_t g_s_trap_handler;

void xsrt_install_strap(xsrt_trap_handler_t fn) {
  g_s_trap_handler = fn;
}

xsrt_trap_frame_t *xsrt_dispatch_strap(xsrt_trap_frame_t *frame) {
  if (g_s_trap_handler == 0) {
    return frame;
  }

  return g_s_trap_handler(frame);
}
