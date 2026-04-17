#include "xsam_noop_platform.h"

#include "xsam/amdev.h"

size_t xsam_noop_input_read(uintptr_t reg, void *buf, size_t size) {
  xsam_dev_input_kbd_t *kbd;

  if (reg != XSAM_DEVREG_INPUT_KBD || buf == 0 || size < sizeof(*kbd)) {
    return 0;
  }

  kbd = (xsam_dev_input_kbd_t *) buf;
  kbd->keydown = 0;
  kbd->keycode = 0;
  return sizeof(*kbd);
}
