#include <stdint.h>

static uint8_t scalar_misalign_load_in_16b_arena[32] __attribute__((aligned(16)));

static uint32_t scalar_misalign_load_lw(const void *ptr) {
  uint32_t value;

  __asm__ volatile(
      "lw %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static uint64_t scalar_misalign_load_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

int main(void) {
  uint8_t *base = &scalar_misalign_load_in_16b_arena[0];
  const uint8_t *lw_ptr = base + 1u;
  const uint8_t *ld_ptr = base + 7u;
  uint32_t lw_value;
  uint64_t ld_value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_load_in_16b_arena); ++index) {
    scalar_misalign_load_in_16b_arena[index] = 0u;
  }

  base[1] = 0x44u;
  base[2] = 0x33u;
  base[3] = 0x22u;
  base[4] = 0x11u;
  lw_value = scalar_misalign_load_lw(lw_ptr);
  if (lw_value != 0x11223344u) {
    return 11;
  }

  base[7] = 0x88u;
  base[8] = 0x77u;
  base[9] = 0x66u;
  base[10] = 0x55u;
  base[11] = 0x44u;
  base[12] = 0x33u;
  base[13] = 0x22u;
  base[14] = 0x11u;
  ld_value = scalar_misalign_load_ld(ld_ptr);
  if (ld_value != 0x1122334455667788ull) {
    return 12;
  }

  return 0;
}
