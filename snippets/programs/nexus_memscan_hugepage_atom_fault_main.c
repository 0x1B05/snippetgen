#include <stdint.h>

#include "xsam/program_snippet.h"
#include "xsam_xs_platform.h"
#include "xsrt_trap.h"

/*
 * Minimal hugepage atom-fault slice derived from sv39_hp_atom_test:
 * prove atomics work on one RW 2 MiB hugepage, then verify:
 * - amoadd.d on an R-only hugepage raises store page fault
 * - lr.d on a W-only hugepage raises load page fault
 */

enum {
  NEXUS_MEMSCAN_CAUSE_LOAD_PAGE = 13u,
  NEXUS_MEMSCAN_CAUSE_STORE_PAGE = 15u,
  NEXUS_MEMSCAN_BAD_HANDLER_COUNT = 91,
  NEXUS_MEMSCAN_BAD_STORE_CAUSE = 92,
  NEXUS_MEMSCAN_BAD_LOAD_CAUSE = 93,
  NEXUS_MEMSCAN_BAD_STORE_TVAL = 94,
  NEXUS_MEMSCAN_BAD_LOAD_TVAL = 95,
  NEXUS_MEMSCAN_BAD_AMO_OLD_VALUE = 96,
  NEXUS_MEMSCAN_BAD_AMO_RW_VALUE = 97,
  NEXUS_MEMSCAN_BAD_LR_RW_VALUE = 98,
  NEXUS_MEMSCAN_MSTATUS_MPP_S = 1u << 11,
  NEXUS_MEMSCAN_MSTATUS_MPRV = 1u << 17,
  NEXUS_MEMSCAN_SATP_MODE_SV39 = 8ull << 60,
  NEXUS_MEMSCAN_PAGE_SHIFT = 12u,
  NEXUS_MEMSCAN_VPN_MASK = 0x1ffu,
  NEXUS_MEMSCAN_PTE_V = 1u << 0,
  NEXUS_MEMSCAN_PTE_R = 1u << 1,
  NEXUS_MEMSCAN_PTE_W = 1u << 2,
  NEXUS_MEMSCAN_PTE_X = 1u << 3,
  NEXUS_MEMSCAN_PTE_A = 1u << 6,
  NEXUS_MEMSCAN_PTE_D = 1u << 7,
};

static const uintptr_t nexus_memscan_huge_rw_va = 0xa00000000ull;
static const uintptr_t nexus_memscan_huge_ro_va = 0xb00000000ull;
static const uintptr_t nexus_memscan_huge_wo_va = 0xc00000000ull;
static const uintptr_t nexus_memscan_runtime_identity_base = 0x80000000ull;
static const uint64_t nexus_memscan_expected_base = 0x445566778899aab0ull;
static const uint64_t nexus_memscan_expected_delta = 0x11ull;

static uint64_t nexus_memscan_root_pt[512] __attribute__((aligned(4096)));
static uint64_t nexus_memscan_l1_tables[3][512] __attribute__((aligned(4096)));
static unsigned char nexus_memscan_huge_backing[2097152] __attribute__((aligned(2097152)));

static volatile uint64_t nexus_memscan_fault_count;
static volatile uint64_t nexus_memscan_fault_causes[2];
static volatile uintptr_t nexus_memscan_fault_tvals[2];
static uintptr_t nexus_memscan_saved_satp;

static unsigned nexus_memscan_vpn2(uintptr_t va) {
  return (unsigned) ((va >> 30) & NEXUS_MEMSCAN_VPN_MASK);
}

static unsigned nexus_memscan_vpn1(uintptr_t va) {
  return (unsigned) ((va >> 21) & NEXUS_MEMSCAN_VPN_MASK);
}

static uint64_t nexus_memscan_make_table_pte(uintptr_t pa) {
  return ((uint64_t) (pa >> NEXUS_MEMSCAN_PAGE_SHIFT) << 10) |
      (uint64_t) NEXUS_MEMSCAN_PTE_V;
}

static uint64_t nexus_memscan_make_leaf_pte(uintptr_t pa, uint64_t flags) {
  return ((uint64_t) (pa >> NEXUS_MEMSCAN_PAGE_SHIFT) << 10) | flags |
      (uint64_t) NEXUS_MEMSCAN_PTE_V;
}

static void nexus_memscan_enable_supervisor_access_window(void) {
  xsam_xs_pmp_init();
}

static void nexus_memscan_map_huge_leaf(
    uintptr_t va,
    uintptr_t pa,
    uint64_t flags,
    uint64_t *l1_table) {
  nexus_memscan_root_pt[nexus_memscan_vpn2(va)] =
      nexus_memscan_make_table_pte((uintptr_t) l1_table);
  l1_table[nexus_memscan_vpn1(va)] = nexus_memscan_make_leaf_pte(pa, flags);
}

static void nexus_memscan_build_sv39_tables(void) {
  const uintptr_t backing_pa = (uintptr_t) nexus_memscan_huge_backing;
  const uint64_t rw_flags = (uint64_t) NEXUS_MEMSCAN_PTE_R |
      (uint64_t) NEXUS_MEMSCAN_PTE_W |
      (uint64_t) NEXUS_MEMSCAN_PTE_A |
      (uint64_t) NEXUS_MEMSCAN_PTE_D;
  const uint64_t ro_flags = (uint64_t) NEXUS_MEMSCAN_PTE_R |
      (uint64_t) NEXUS_MEMSCAN_PTE_A |
      (uint64_t) NEXUS_MEMSCAN_PTE_D;
  const uint64_t wo_flags = (uint64_t) NEXUS_MEMSCAN_PTE_W |
      (uint64_t) NEXUS_MEMSCAN_PTE_A |
      (uint64_t) NEXUS_MEMSCAN_PTE_D;
  const uint64_t identity_flags = (uint64_t) NEXUS_MEMSCAN_PTE_R |
      (uint64_t) NEXUS_MEMSCAN_PTE_W |
      (uint64_t) NEXUS_MEMSCAN_PTE_X |
      (uint64_t) NEXUS_MEMSCAN_PTE_A |
      (uint64_t) NEXUS_MEMSCAN_PTE_D;

  nexus_memscan_root_pt[nexus_memscan_vpn2(nexus_memscan_runtime_identity_base)] =
      nexus_memscan_make_leaf_pte(nexus_memscan_runtime_identity_base, identity_flags);

  nexus_memscan_map_huge_leaf(
      nexus_memscan_huge_rw_va,
      backing_pa,
      rw_flags,
      nexus_memscan_l1_tables[0]);
  nexus_memscan_map_huge_leaf(
      nexus_memscan_huge_ro_va,
      backing_pa,
      ro_flags,
      nexus_memscan_l1_tables[1]);
  nexus_memscan_map_huge_leaf(
      nexus_memscan_huge_wo_va,
      backing_pa,
      wo_flags,
      nexus_memscan_l1_tables[2]);
}

static void nexus_memscan_install_sv39_root(void) {
  uintptr_t satp_value;

  nexus_memscan_build_sv39_tables();
  __asm__ volatile("csrr %0, satp" : "=r"(nexus_memscan_saved_satp) : : "memory");
  satp_value = (uintptr_t) NEXUS_MEMSCAN_SATP_MODE_SV39 |
      ((uintptr_t) nexus_memscan_root_pt >> NEXUS_MEMSCAN_PAGE_SHIFT);
  __asm__ volatile("csrw satp, %0" : : "r"(satp_value) : "memory");
  __asm__ volatile("sfence.vma x0, x0" : : : "memory");
}

static void nexus_memscan_restore_sv39_root(void) {
  __asm__ volatile("csrw satp, %0" : : "r"(nexus_memscan_saved_satp) : "memory");
  __asm__ volatile("sfence.vma x0, x0" : : : "memory");
}

static void nexus_memscan_faulting_store(uintptr_t addr, uint64_t value) {
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "sd %1, 0(%0)\n\t"
      "csrw mstatus, t0\n\t"
      :
      : "r"(addr), "r"(value), "r"(new_status)
      : "t0", "memory");
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

static void nexus_memscan_faulting_amoadd(uintptr_t addr, uint64_t value) {
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "amoadd.d zero, %1, (%0)\n\t"
      "csrw mstatus, t0\n\t"
      :
      : "r"(addr), "r"(value), "r"(new_status)
      : "t0", "memory");
}

static uint64_t nexus_memscan_faulting_amoadd_read_old(uintptr_t addr, uint64_t value) {
  uint64_t old_value = 0u;
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %3\n\t"
      "amoadd.d %0, %2, (%1)\n\t"
      "csrw mstatus, t0\n\t"
      : "=r"(old_value)
      : "r"(addr), "r"(value), "r"(new_status)
      : "t0", "memory");
  return old_value;
}

static uint64_t nexus_memscan_faulting_lr(uintptr_t addr) {
  uint64_t value = 0u;
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPP_S |
      (uintptr_t) NEXUS_MEMSCAN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "lr.d %0, (%1)\n\t"
      "csrw mstatus, t0\n\t"
      : "=r"(value)
      : "r"(addr), "r"(new_status)
      : "t0", "memory");
  return value;
}

static uintptr_t nexus_memscan_insn_len(uintptr_t pc) {
  uint16_t insn_lo = *(volatile uint16_t *) pc;
  return ((insn_lo & 0x3u) == 0x3u) ? 4u : 2u;
}

static xsrt_trap_frame_t *nexus_memscan_hugepage_atom_fault_handler(xsrt_trap_frame_t *frame) {
  if (nexus_memscan_fault_count < 2u) {
    nexus_memscan_fault_causes[nexus_memscan_fault_count] = frame->cause;
    nexus_memscan_fault_tvals[nexus_memscan_fault_count] = (uintptr_t) frame->tval;
  }
  nexus_memscan_fault_count += 1u;
  frame->epc += nexus_memscan_insn_len(frame->epc);
  return frame;
}

int main(void) {
  volatile uint64_t sink = 0u;
  uint64_t amo_old_value;
  uint64_t rw_value_after_amo;
  uint64_t lr_rw_value;

  nexus_memscan_fault_count = 0u;
  nexus_memscan_fault_causes[0] = 0u;
  nexus_memscan_fault_causes[1] = 0u;
  nexus_memscan_fault_tvals[0] = 0u;
  nexus_memscan_fault_tvals[1] = 0u;
  nexus_memscan_saved_satp = 0u;

  xsrt_install_strap(nexus_memscan_hugepage_atom_fault_handler);
  nexus_memscan_enable_supervisor_access_window();
  nexus_memscan_install_sv39_root();

  nexus_memscan_faulting_store(nexus_memscan_huge_rw_va, nexus_memscan_expected_base);
  amo_old_value = nexus_memscan_faulting_amoadd_read_old(
      nexus_memscan_huge_rw_va,
      nexus_memscan_expected_delta);
  rw_value_after_amo = nexus_memscan_faulting_load(nexus_memscan_huge_rw_va);
  lr_rw_value = nexus_memscan_faulting_lr(nexus_memscan_huge_rw_va);

  if (amo_old_value != nexus_memscan_expected_base) {
    nexus_memscan_restore_sv39_root();
    xsrt_install_strap(0);
    return NEXUS_MEMSCAN_BAD_AMO_OLD_VALUE;
  }

  if (rw_value_after_amo != nexus_memscan_expected_base + nexus_memscan_expected_delta) {
    nexus_memscan_restore_sv39_root();
    xsrt_install_strap(0);
    return NEXUS_MEMSCAN_BAD_AMO_RW_VALUE;
  }

  if (lr_rw_value != nexus_memscan_expected_base + nexus_memscan_expected_delta) {
    nexus_memscan_restore_sv39_root();
    xsrt_install_strap(0);
    return NEXUS_MEMSCAN_BAD_LR_RW_VALUE;
  }

  nexus_memscan_faulting_amoadd(nexus_memscan_huge_ro_va, nexus_memscan_expected_delta);
  sink = nexus_memscan_faulting_lr(nexus_memscan_huge_wo_va);
  (void) sink;

  nexus_memscan_restore_sv39_root();
  xsrt_install_strap(0);

  if (nexus_memscan_fault_count != 2u) {
    return NEXUS_MEMSCAN_BAD_HANDLER_COUNT;
  }

  if (nexus_memscan_fault_causes[0] != NEXUS_MEMSCAN_CAUSE_STORE_PAGE) {
    return NEXUS_MEMSCAN_BAD_STORE_CAUSE;
  }

  if (nexus_memscan_fault_causes[1] != NEXUS_MEMSCAN_CAUSE_LOAD_PAGE) {
    return NEXUS_MEMSCAN_BAD_LOAD_CAUSE;
  }

  if (nexus_memscan_fault_tvals[0] != nexus_memscan_huge_ro_va) {
    return NEXUS_MEMSCAN_BAD_STORE_TVAL;
  }

  if (nexus_memscan_fault_tvals[1] != nexus_memscan_huge_wo_va) {
    return NEXUS_MEMSCAN_BAD_LOAD_TVAL;
  }

  return 0;
}
