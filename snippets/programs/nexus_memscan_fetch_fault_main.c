#include <stdint.h>

#include "xsam/program_snippet.h"
#include "xsrt_trap.h"

/*
 * Minimal memscantest-derived execute-fault slice:
 * lock a PMP deny window so M-mode fetch is constrained, jump into it, then
 * let the trap handler rewrite EPC to a known resume label.
 */

enum {
  NEXUS_MEMSCAN_CAUSE_FETCH_ACCESS = 1u,
  NEXUS_MEMSCAN_BAD_HANDLER_COUNT = 31,
  NEXUS_MEMSCAN_BAD_FETCH_CAUSE = 32,
  NEXUS_MEMSCAN_PMP_LOCK = 1u << 7,
};

static volatile uint64_t nexus_memscan_fetch_fault_count;
static volatile uint64_t nexus_memscan_fetch_last_cause;
static volatile uintptr_t nexus_memscan_fetch_resume_pc;

static void nexus_memscan_enable_exec_fault_window(void) {
  const uintptr_t allow_all_s_mode = (uintptr_t) 31u << (8u * 7u);
  const uintptr_t deny_addr = (0x90000000ull | ((0x10000ull >> 1) - 1ull)) >> 2;
  const uintptr_t deny_napot_locked = (uintptr_t) NEXUS_MEMSCAN_PMP_LOCK | ((uintptr_t) 3u << 3);

  __asm__ volatile("csrw pmpaddr15, %0" : : "r"(~(uintptr_t) 0) : "memory");
  __asm__ volatile("csrw pmpcfg2, %0" : : "r"(allow_all_s_mode) : "memory");
  __asm__ volatile("csrw pmpaddr1, %0" : : "r"(deny_addr) : "memory");
  __asm__ volatile("csrw pmpcfg0, %0" : : "r"(deny_napot_locked << 8) : "memory");
  __asm__ volatile("sfence.vma x0, x0" : : : "memory");
}

static xsrt_trap_frame_t *nexus_memscan_fetch_fault_handler(xsrt_trap_frame_t *frame) {
  nexus_memscan_fetch_fault_count += 1u;
  nexus_memscan_fetch_last_cause = frame->cause;
  frame->epc = nexus_memscan_fetch_resume_pc;
  return frame;
}

static void nexus_memscan_trigger_fetch_fault(uintptr_t addr) {
  __asm__ volatile(
      "la t0, 1f\n\t"
      "sd t0, %0\n\t"
      "fence.i\n\t"
      "jr %1\n\t"
      "1:\n\t"
      : "=m"(nexus_memscan_fetch_resume_pc)
      : "r"(addr)
      : "t0", "memory");
}

int main(void) {
  nexus_memscan_fetch_fault_count = 0u;
  nexus_memscan_fetch_last_cause = 0u;
  nexus_memscan_fetch_resume_pc = 0u;

  nexus_memscan_enable_exec_fault_window();
  xsrt_install_strap(nexus_memscan_fetch_fault_handler);
  nexus_memscan_trigger_fetch_fault(0x90000000ull);
  xsrt_install_strap(0);

  if (nexus_memscan_fetch_fault_count != 1u) {
    return NEXUS_MEMSCAN_BAD_HANDLER_COUNT;
  }

  if (nexus_memscan_fetch_last_cause != NEXUS_MEMSCAN_CAUSE_FETCH_ACCESS) {
    return NEXUS_MEMSCAN_BAD_FETCH_CAUSE;
  }

  return 0;
}
