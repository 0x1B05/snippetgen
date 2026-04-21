#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static int check_replay_probe_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_REPLAY_SUMMARY) & 0xffff0000u) !=
      (XS_SCALAR_MISALIGN_REPLAY_PROBE_MAGIC & 0xffff0000u)) {
    return 461;
  }

  if ((xsrt_csr_read(XS_SCALAR_MISALIGN_CSR_REPLAY_SUMMARY) ^ XS_SCALAR_MISALIGN_REPLAY_PROBE_MAGIC) < 4u) {
    return 462;
  }

  return 0;
}

const xsrt_snippet_desc_t snippet_check_replay_probe = {
  .id = "check_replay_probe",
  .check = check_replay_probe_check,
};
