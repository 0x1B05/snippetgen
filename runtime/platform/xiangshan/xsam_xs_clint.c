#include "xsam_xs_platform.h"

#include "xsam/amdev.h"

enum {
  XSAM_XS_UART_ADDR = 0x40600000u,
};

#define XSAM_XS_RTC_ADDR ((volatile uint64_t *) 0x3800bff8ull)
#define XSAM_XS_MTIMECMP_ADDR ((volatile uint64_t *) 0x38004000ull)

uint64_t xsam_xs_clint_mtime_addr(void) {
  return (uint64_t) (uintptr_t) XSAM_XS_RTC_ADDR;
}

uint64_t xsam_xs_clint_mtimecmp_addr(void) {
  return (uint64_t) (uintptr_t) XSAM_XS_MTIMECMP_ADDR;
}

uint64_t xsam_xs_clint_read_mtime(void) {
  return *XSAM_XS_RTC_ADDR;
}

uint64_t xsam_xs_clint_read_mtimecmp(void) {
  return *XSAM_XS_MTIMECMP_ADDR;
}

void xsam_xs_clint_write_mtimecmp(uint64_t value) {
  *XSAM_XS_MTIMECMP_ADDR = value;
}

size_t xsam_xs_clint_read_uptime(uintptr_t reg, void *buf, size_t size) {
  xsam_dev_timer_uptime_t *uptime;
  uint64_t ticks;

  if (reg != XSAM_DEVREG_TIMER_UPTIME || buf == 0 || size < sizeof(*uptime)) {
    return 0;
  }

  ticks = xsam_xs_clint_read_mtime();
  uptime = (xsam_dev_timer_uptime_t *) buf;
  uptime->hi = (uint32_t) (ticks >> 32);
  uptime->lo = (uint32_t) ticks;
  return sizeof(*uptime);
}

size_t xsam_xs_serial_write(uintptr_t reg, const void *buf, size_t size) {
  const xsam_dev_serial_send_t *payload;

  if (reg != XSAM_DEVREG_SERIAL_SEND || buf == 0 || size < sizeof(*payload)) {
    return 0;
  }

  payload = (const xsam_dev_serial_send_t *) buf;
  *((volatile uint8_t *) (uintptr_t) XSAM_XS_UART_ADDR) = payload->data;
  return sizeof(*payload);
}

size_t xsam_xs_input_read(uintptr_t reg, void *buf, size_t size) {
  xsam_dev_input_kbd_t *kbd;

  if (reg != XSAM_DEVREG_INPUT_KBD || buf == 0 || size < sizeof(*kbd)) {
    return 0;
  }

  kbd = (xsam_dev_input_kbd_t *) buf;
  kbd->keydown = 0;
  kbd->keycode = 0;
  return sizeof(*kbd);
}

size_t xsam_xs_perf_read(uintptr_t reg, void *buf, size_t size) {
  uint64_t *counter;

  if (reg != XSAM_DEVREG_PERFCNT_CYCLE || buf == 0 || size < sizeof(*counter)) {
    return 0;
  }

  counter = (uint64_t *) buf;
  *counter = 0u;
  return sizeof(*counter);
}
