#ifndef XSAM_VME_H
#define XSAM_VME_H

#include <stddef.h>

#include "xsam/am.h"

enum {
  XSAM_VME_MAP_NORMAL = 0,
  XSAM_VME_MAP_FAULT = 1,
  XSAM_VME_MAP_HUGEPAGE = 2,
};

struct xsam_address_space {
  size_t pgsize;
  xsam_area_t area;
  void *ptr;
};

size_t xsam_vme_mapping_count(const xsam_address_space_t *as);
int xsam_vme_lookup(
    const xsam_address_space_t *as,
    void *va,
    void **pa_out,
    int *prot_out,
    int *kind_out,
    int *level_out);

#endif
