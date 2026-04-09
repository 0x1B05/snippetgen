#ifndef XSRT_CSR_H
#define XSRT_CSR_H

#include <stdint.h>

uint64_t xsrt_csr_read(uint32_t csr);
void xsrt_csr_write(uint32_t csr, uint64_t val);

#endif
