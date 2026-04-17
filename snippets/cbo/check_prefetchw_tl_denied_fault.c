#include <stdint.h>

#include "xs_prefetchw.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"


static int check_prefetchw_tl_denied_fault_check(xsrt_env_t *env) {
  uint64_t trap_count;

  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_PREFETCHW_FLAG_COMPLETED) == 0u) {
    return 91;
  }

  if ((env->flags & (uint64_t) XS_PREFETCHW_FLAG_LOAD_PHASE_COMPLETED) == 0u) {
    return 92;
  }

  if ((env->flags & (uint64_t) XS_PREFETCHW_FLAG_PREFETCH_PHASE_COMPLETED) == 0u) {
    return 93;
  }

  if (xs_prefetchw_completed == 0u) {
    return 94;
  }

  if (env->interrupt_count != 0u) {
    return 95;
  }

  if (xs_prefetchw_phase != (uint64_t) XS_PREFETCHW_PHASE_NONE) {
    return 96;
  }

  /* The final expected ledger is: one load trap, then a no-trap prefetch.w. */
  trap_count = xs_prefetchw_trap_count;
  if (trap_count != 1u) {
    return 97;
  }

  if (xs_prefetchw_target_addr != XS_PREFETCHW_TARGET_ADDR) {
    return 98;
  }

  if (env->snippet_id != trap_count) {
    return 99;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_TRAP_COUNT) != trap_count) {
    return 100;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_TARGET_ADDR) != XS_PREFETCHW_TARGET_ADDR) {
    return 101;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_LOAD_VALUE) != xs_prefetchw_load_value) {
    return 102;
  }

  /* The only software-visible exception in this case must come from the load. */
  if (xs_prefetchw_last_phase != (uint64_t) XS_PREFETCHW_PHASE_LOAD) {
    return 113;
  }

  if (xs_prefetchw_last_cause != (uint64_t) XS_PREFETCHW_EXPECTED_TRAP_CAUSE) {
    return 114;
  }

  if (xs_prefetchw_last_epc == 0u) {
    return 115;
  }

  if (env->last_trap_cause != xs_prefetchw_last_cause) {
    return 116;
  }

  if (env->last_trap_epc != xs_prefetchw_last_epc) {
    return 117;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_LAST_PHASE) != xs_prefetchw_last_phase) {
    return 118;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_LAST_CAUSE) != xs_prefetchw_last_cause) {
    return 119;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_LAST_TVAL) != xs_prefetchw_last_tval) {
    return 120;
  }

  if (xsrt_csr_read(XS_PREFETCHW_DEBUG_CSR_LAST_EPC) != xs_prefetchw_last_epc) {
    return 121;
  }

  return 0;
}


const xsrt_snippet_desc_t snippet_check_prefetchw_tl_denied_fault = {
  .id = "check_prefetchw_tl_denied_fault",
  .check = check_prefetchw_tl_denied_fault_check,
};
