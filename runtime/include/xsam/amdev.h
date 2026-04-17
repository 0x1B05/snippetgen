#ifndef XSAM_AMDEV_H
#define XSAM_AMDEV_H

#include <stdint.h>

#define XSAM_DEV_PERFCNT 0x0000ac01u
#define XSAM_DEV_INPUT 0x0000ac02u
#define XSAM_DEV_TIMER 0x0000ac03u
#define XSAM_DEV_VIDEO 0x0000ac04u
#define XSAM_DEV_SERIAL 0x0000ac05u
#define XSAM_DEV_STORAGE 0x0000ac06u
#define XSAM_DEV_AUDIO 0x0000ac07u
#define XSAM_DEV_PCICONF 0x00000080u

enum {
  XSAM_DEVREG_PERFCNT_CYCLE = 1u,
  XSAM_DEVREG_INPUT_KBD = 1u,
  XSAM_DEVREG_TIMER_UPTIME = 1u,
  XSAM_DEVREG_TIMER_DATE = 2u,
  XSAM_DEVREG_SERIAL_RECV = 1u,
  XSAM_DEVREG_SERIAL_SEND = 2u,
  XSAM_DEVREG_SERIAL_STAT = 3u,
  XSAM_DEVREG_SERIAL_CTRL = 4u,
};

typedef struct { uint32_t hi, lo; } __attribute__((packed)) xsam_dev_timer_uptime_t;
typedef struct { int year, month, day, hour, minute, second; } __attribute__((packed)) xsam_dev_timer_date_t;
typedef struct { int keydown, keycode; } __attribute__((packed)) xsam_dev_input_kbd_t;
typedef struct { uint8_t data; } __attribute__((packed)) xsam_dev_serial_recv_t;
typedef struct { uint8_t data; } __attribute__((packed)) xsam_dev_serial_send_t;
typedef struct { uint8_t data; } __attribute__((packed)) xsam_dev_serial_stat_t;
typedef struct { uint8_t data; } __attribute__((packed)) xsam_dev_serial_ctrl_t;

#endif
