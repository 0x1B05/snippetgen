#include <stdint.h>

#include "xsam/program_snippet.h"
#include "xsam_xs_platform.h"
#include "xsrt_trap.h"

/*
 * Minimal port derived from nexus-am/tests/memscantest:
 * install a machine trap handler, trigger one expected load access fault,
 * then resume execution after the faulting instruction.
 */

enum {
  NEXUS_MEMSCAN_CAUSE_LOAD_ACCESS = 5u,
  NEXUS_MEMSCAN_CAUSE_STORE_ACCESS = 7u,
  NEXUS_MEMSCAN_BAD_HANDLER_COUNT = 21,
  NEXUS_MEMSCAN_BAD_LOAD_CAUSE = 22,
  NEXUS_MEMSCAN_BAD_STORE_CAUSE = 23,
  NEXUS_MEMSCAN_MSTATUS_MPP_S = 1u << 11,
  NEXUS_MEMSCAN_MSTATUS_MPRV = 1u << 17,
};

static volatile uint64_t nexus_memscan_fault_count;
static volatile uint64_t nexus_memscan_fault_causes[2];

static void nexus_memscan_enable_fault_window(void) {
  const uintptr_t allow_all_entry = XSAM_XS_PMP_COUNT - 1u;

  (void) allow_all_entry;
  xsam_xs_pmp_init();
  xsam_xs_pmp_enable_napot(1u, 0x90000000ull, 0x10000ull, 0u, 0u);
}

static uint64_t nexus_memscan_faulting_load(uintptr_t addr) {
  uint64_t value = 0u;
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "ld %0, 0(%1)\n\t"
      "csrw mstatus, t0\n\t"
      : "=r"(value)
      : "r"(addr), "r"(new_status)
      : "t0", "memory");
  return value;
}

static void nexus_memscan_faulting_store(uintptr_t addr) {
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %1\n\t"
      "sd zero, 0(%0)\n\t"
      "csrw mstatus, t0\n\t"
      :
      : "r"(addr), "r"(new_status)
      : "t0", "memory");
}

static uintptr_t nexus_memscan_insn_len(uintptr_t pc) {
  uint16_t insn_lo = *(volatile uint16_t *) pc;
  return ((insn_lo & 0x3u) == 0x3u) ? 4u : 2u;
}

static xsrt_trap_frame_t *nexus_memscan_access_fault_handler(xsrt_trap_frame_t *frame) {
  if (nexus_memscan_fault_count < 2u) {
    nexus_memscan_fault_causes[nexus_memscan_fault_count] = frame->cause;
  }
  nexus_memscan_fault_count += 1u;
  frame->epc += nexus_memscan_insn_len(frame->epc);
  return frame;
}

int main(void) {
  volatile uint64_t sink = 0u;

  nexus_memscan_fault_count = 0u;
  nexus_memscan_fault_causes[0] = 0u;
  nexus_memscan_fault_causes[1] = 0u;

  nexus_memscan_enable_fault_window();
  xsrt_install_strap(nexus_memscan_access_fault_handler);
  sink = nexus_memscan_faulting_load(0x90000000ull);
  nexus_memscan_faulting_store(0x90000000ull);
  (void) sink;
  xsrt_install_strap(0);

  if (nexus_memscan_fault_count != 2u) {
    return NEXUS_MEMSCAN_BAD_HANDLER_COUNT;
  }

  if (nexus_memscan_fault_causes[0] != NEXUS_MEMSCAN_CAUSE_LOAD_ACCESS) {
    return NEXUS_MEMSCAN_BAD_LOAD_CAUSE;
  }

  if (nexus_memscan_fault_causes[1] != NEXUS_MEMSCAN_CAUSE_STORE_ACCESS) {
    return NEXUS_MEMSCAN_BAD_STORE_CAUSE;
  }

  return 0;
}
