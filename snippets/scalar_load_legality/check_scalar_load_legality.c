#include <stdint.h>

#include "xs_snippet.h"
#include "xsrt_csr.h"


enum {
  EXPECTED_UNALIGNED_VALUE = 0x12345678u,
};


static int check_scalar_load_legality_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) 0x10u) == 0u) {
    return 41;
  }

  if (env->snippet_id != EXPECTED_UNALIGNED_VALUE) {
    return 42;
  }

  if (xsrt_csr_read(7u) != EXPECTED_UNALIGNED_VALUE) {
    return 43;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_scalar_load_legality = {
  .id = "check_scalar_load_legality",
  .check = check_scalar_load_legality_check,
};
