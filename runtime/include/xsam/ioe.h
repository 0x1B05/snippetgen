#ifndef XSAM_IOE_H
#define XSAM_IOE_H

#include <stddef.h>
#include <stdint.h>

#include "xsam/amdev.h"

int xsam_ioe_init(void);
size_t xsam_io_read(uint32_t dev, uintptr_t reg, void *buf, size_t size);
size_t xsam_io_write(uint32_t dev, uintptr_t reg, const void *buf, size_t size);

#endif
