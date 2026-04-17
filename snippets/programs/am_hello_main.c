#include "xsam/am.h"
#include "xsam/amdev.h"
#include "xsam/ioe.h"
#include "xsam/program_snippet.h"

int main(void) {
  xsrt_env_t *env = xsam_current_env();
  xsam_dev_timer_uptime_t uptime;
  xsam_dev_serial_send_t serial;

  if (env == 0) {
    return 11;
  }

  if (xsam_ioe_init() != 0) {
    return 12;
  }

  if (xsam_io_read(XSAM_DEV_TIMER, XSAM_DEVREG_TIMER_UPTIME, &uptime, sizeof(uptime)) != sizeof(uptime)) {
    return 13;
  }

  serial.data = (uint8_t) 'H';
  if (xsam_io_write(XSAM_DEV_SERIAL, XSAM_DEVREG_SERIAL_SEND, &serial, sizeof(serial)) != sizeof(serial)) {
    return 14;
  }

  env->flags |= (1ull << 8) | (1ull << 9);
  return 0;
}
