#include <stddef.h>
#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsam_xs_platform.h"
#include "xsrt_csr.h"
#include "xsrt_trap.h"

enum {
  XS_SCALAR_MISALIGN_MSTATUS_MPP_S = 1u << 11,
  XS_SCALAR_MISALIGN_MSTATUS_MPRV = 1u << 17,
  XS_SCALAR_MISALIGN_SATP_MODE_SV39 = 8ull << 60,
  XS_SCALAR_MISALIGN_PAGE_SHIFT = 12u,
  XS_SCALAR_MISALIGN_VPN_MASK = 0x1ffu,
  XS_SCALAR_MISALIGN_PTE_V = 1u << 0,
  XS_SCALAR_MISALIGN_PTE_R = 1u << 1,
  XS_SCALAR_MISALIGN_PTE_W = 1u << 2,
  XS_SCALAR_MISALIGN_PTE_X = 1u << 3,
  XS_SCALAR_MISALIGN_PTE_A = 1u << 6,
  XS_SCALAR_MISALIGN_PTE_D = 1u << 7,
};

static const uintptr_t xs_scalar_misalign_search_load_base_va = 0x910000000ull;
static const uintptr_t xs_scalar_misalign_search_store_base_va = 0xa10000000ull;
static const uintptr_t xs_scalar_misalign_search_fault_pa = 0x90000000ull;
static const uintptr_t xs_scalar_misalign_search_runtime_identity_base = 0x80000000ull;

static uint64_t xs_scalar_misalign_search_root_pt[512] __attribute__((aligned(4096)));
static uint64_t xs_scalar_misalign_search_l1_tables[2][512] __attribute__((aligned(4096)));
static uint64_t xs_scalar_misalign_search_l0_tables[2][512] __attribute__((aligned(4096)));
static unsigned char xs_scalar_misalign_search_load_backing[2][4096] __attribute__((aligned(4096)));
static unsigned char xs_scalar_misalign_search_store_backing[4096] __attribute__((aligned(4096)));

static volatile uint64_t xs_scalar_misalign_search_fault_count;
static volatile uint64_t xs_scalar_misalign_search_fault_causes[2];
static volatile uintptr_t xs_scalar_misalign_search_fault_tvals[2];
static uintptr_t xs_scalar_misalign_search_saved_satp;

static unsigned xs_scalar_misalign_search_vpn2(uintptr_t va) {
  return (unsigned) ((va >> 30) & XS_SCALAR_MISALIGN_VPN_MASK);
}

static unsigned xs_scalar_misalign_search_vpn1(uintptr_t va) {
  return (unsigned) ((va >> 21) & XS_SCALAR_MISALIGN_VPN_MASK);
}

static unsigned xs_scalar_misalign_search_vpn0(uintptr_t va) {
  return (unsigned) ((va >> 12) & XS_SCALAR_MISALIGN_VPN_MASK);
}

static uint64_t xs_scalar_misalign_search_make_table_pte(uintptr_t pa) {
  return ((uint64_t) (pa >> XS_SCALAR_MISALIGN_PAGE_SHIFT) << 10) |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_V;
}

static uint64_t xs_scalar_misalign_search_make_leaf_pte(uintptr_t pa, uint64_t flags) {
  return ((uint64_t) (pa >> XS_SCALAR_MISALIGN_PAGE_SHIFT) << 10) | flags |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_V;
}

static void xs_scalar_misalign_search_map_two_page_region(
    uintptr_t va,
    uintptr_t pa0,
    uintptr_t pa1,
    uint64_t flags0,
    uint64_t flags1,
    uint64_t *l1_table,
    uint64_t *l0_table) {
  xs_scalar_misalign_search_root_pt[xs_scalar_misalign_search_vpn2(va)] =
      xs_scalar_misalign_search_make_table_pte((uintptr_t) l1_table);
  l1_table[xs_scalar_misalign_search_vpn1(va)] =
      xs_scalar_misalign_search_make_table_pte((uintptr_t) l0_table);
  l0_table[xs_scalar_misalign_search_vpn0(va)] =
      xs_scalar_misalign_search_make_leaf_pte(pa0, flags0);
  l0_table[xs_scalar_misalign_search_vpn0(va + 4096u)] =
      xs_scalar_misalign_search_make_leaf_pte(pa1, flags1);
}

static void xs_scalar_misalign_search_configure_pmp(void) {
  xsam_xs_pmp_init();
  xsam_xs_pmp_enable_napot(1u, xs_scalar_misalign_search_fault_pa, 0x10000ull, 0u, 0u);
}

static void xs_scalar_misalign_search_build_tables(void) {
  const uint64_t rw_flags = (uint64_t) XS_SCALAR_MISALIGN_PTE_R |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_W |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_A |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_D;
  const uint64_t page_fault_flags = (uint64_t) XS_SCALAR_MISALIGN_PTE_A |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_D;
  const uint64_t identity_flags = (uint64_t) XS_SCALAR_MISALIGN_PTE_R |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_W |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_X |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_A |
      (uint64_t) XS_SCALAR_MISALIGN_PTE_D;

  xs_scalar_misalign_search_root_pt[xs_scalar_misalign_search_vpn2(xs_scalar_misalign_search_runtime_identity_base)] =
      xs_scalar_misalign_search_make_leaf_pte(xs_scalar_misalign_search_runtime_identity_base, identity_flags);

  xs_scalar_misalign_search_map_two_page_region(
      xs_scalar_misalign_search_load_base_va,
      (uintptr_t) xs_scalar_misalign_search_load_backing[0],
      (uintptr_t) xs_scalar_misalign_search_load_backing[1],
      rw_flags,
      page_fault_flags,
      xs_scalar_misalign_search_l1_tables[0],
      xs_scalar_misalign_search_l0_tables[0]);
  xs_scalar_misalign_search_map_two_page_region(
      xs_scalar_misalign_search_store_base_va,
      (uintptr_t) xs_scalar_misalign_search_store_backing,
      xs_scalar_misalign_search_fault_pa,
      rw_flags,
      rw_flags,
      xs_scalar_misalign_search_l1_tables[1],
      xs_scalar_misalign_search_l0_tables[1]);
}

static void xs_scalar_misalign_search_install_root(void) {
  uintptr_t satp_value;

  xs_scalar_misalign_search_build_tables();
  __asm__ volatile("csrr %0, satp" : "=r"(xs_scalar_misalign_search_saved_satp) : : "memory");
  satp_value = (uintptr_t) XS_SCALAR_MISALIGN_SATP_MODE_SV39 |
      ((uintptr_t) xs_scalar_misalign_search_root_pt >> XS_SCALAR_MISALIGN_PAGE_SHIFT);
  __asm__ volatile("csrw satp, %0" : : "r"(satp_value) : "memory");
  __asm__ volatile("sfence.vma x0, x0" : : : "memory");
}

static void xs_scalar_misalign_search_restore_root(void) {
  __asm__ volatile("csrw satp, %0" : : "r"(xs_scalar_misalign_search_saved_satp) : "memory");
  __asm__ volatile("sfence.vma x0, x0" : : : "memory");
}

static uint64_t xs_scalar_misalign_search_faulting_load(uintptr_t addr) {
  uint64_t value = 0u;
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) XS_SCALAR_MISALIGN_MSTATUS_MPP_S |
      (uintptr_t) XS_SCALAR_MISALIGN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "ld %0, 0(%1)\n\t"
      "csrw mstatus, t0\n\t"
      : "=r"(value)
      : "r"(addr), "r"(new_status)
      : "t0", "memory");
  return value;
}

static void xs_scalar_misalign_search_faulting_store(uintptr_t addr, uint64_t value) {
  uintptr_t new_status;

  __asm__ volatile("csrr %0, mstatus" : "=r"(new_status) : : "memory");
  new_status = (new_status & ~((uintptr_t) (3u << 11))) |
      (uintptr_t) XS_SCALAR_MISALIGN_MSTATUS_MPP_S |
      (uintptr_t) XS_SCALAR_MISALIGN_MSTATUS_MPRV;

  __asm__ volatile(
      "csrrw t0, mstatus, %2\n\t"
      "sd %1, 0(%0)\n\t"
      "csrw mstatus, t0\n\t"
      :
      : "r"(addr), "r"(value), "r"(new_status)
      : "t0", "memory");
}

static uintptr_t xs_scalar_misalign_search_insn_len(uintptr_t pc) {
  uint16_t insn_lo = *(volatile uint16_t *) pc;
  return ((insn_lo & 0x3u) == 0x3u) ? 4u : 2u;
}

static xsrt_trap_frame_t *xs_scalar_misalign_search_handler(xsrt_trap_frame_t *frame) {
  if (xs_scalar_misalign_search_fault_count < 2u) {
    xs_scalar_misalign_search_fault_causes[xs_scalar_misalign_search_fault_count] = frame->cause;
    xs_scalar_misalign_search_fault_tvals[xs_scalar_misalign_search_fault_count] = (uintptr_t) frame->tval;
  }
  xs_scalar_misalign_search_fault_count += 1u;
  frame->epc += xs_scalar_misalign_search_insn_len(frame->epc);
  return frame;
}

static int cross_page_fault_search_run(xsrt_env_t *env) {
  static const uint16_t offsets[] = {4095u};
  unsigned repeats;
  volatile uint64_t sink = 0u;

  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_SEARCH_ENTERED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, 0u);

  repeats = 1u + (unsigned) ((env->seed >> 8) & 0x0u);

  xsrt_install_strap(xs_scalar_misalign_search_handler);
  xs_scalar_misalign_search_configure_pmp();
  xs_scalar_misalign_search_install_root();

  for (unsigned round = 0; round < repeats; ++round) {
    const uintptr_t load_ptr = xs_scalar_misalign_search_load_base_va + offsets[0];
    const uintptr_t store_ptr = xs_scalar_misalign_search_store_base_va + offsets[0];

    xs_scalar_misalign_search_fault_count = 0u;
    xs_scalar_misalign_search_fault_causes[0] = 0u;
    xs_scalar_misalign_search_fault_causes[1] = 0u;
    xs_scalar_misalign_search_fault_tvals[0] = 0u;
    xs_scalar_misalign_search_fault_tvals[1] = 0u;

    sink = xs_scalar_misalign_search_faulting_load(load_ptr);
    (void) sink;
    xs_scalar_misalign_search_faulting_store(store_ptr, 0x1122334455667788ull ^ round);

    if (xs_scalar_misalign_search_fault_count != 2u ||
        xs_scalar_misalign_search_fault_causes[0] != XS_SCALAR_MISALIGN_LOAD_PAGE_CAUSE ||
        xs_scalar_misalign_search_fault_causes[1] != XS_SCALAR_MISALIGN_STORE_ACCESS_CAUSE ||
        xs_scalar_misalign_search_fault_tvals[0] != xs_scalar_misalign_search_load_base_va + 4096u ||
        xs_scalar_misalign_search_fault_tvals[1] != xs_scalar_misalign_search_store_base_va + 4096u) {
      xs_scalar_misalign_search_restore_root();
      xsrt_install_strap(0);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 351u + round);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE0, xs_scalar_misalign_search_fault_causes[0]);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE1, xs_scalar_misalign_search_fault_causes[1]);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE2, xs_scalar_misalign_search_fault_tvals[0]);
      return XS_SCALAR_MISALIGN_RC_CROSS_PAGE_SEARCH + (int) round;
    }
  }

  xs_scalar_misalign_search_restore_root();
  xsrt_install_strap(0);

  env->snippet_id = XS_SCALAR_MISALIGN_CROSS_PAGE_SEARCH_MAGIC ^ (uint64_t) repeats;
  env->flags |= (uint64_t) XS_SCALAR_MISALIGN_FLAG_CROSS_PAGE_SEARCH_COMPLETED;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, repeats);
  return 0;
}

const xsrt_snippet_desc_t snippet_cross_page_fault_search = {
  .id = "cross_page_fault_search",
  .run = cross_page_fault_search_run,
};
