#include <stdint.h>

static uint8_t scalar_misalign_load_cross_16b_arena[48] __attribute__((aligned(16)));

static uint64_t scalar_misalign_cross_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

int main(void) {
  uint8_t *base = &scalar_misalign_load_cross_16b_arena[0];
  const uint8_t *ptr = base + 13u;
  uint64_t value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_load_cross_16b_arena); ++index) {
    scalar_misalign_load_cross_16b_arena[index] = 0u;
  }

  base[13] = 0x88u;
  base[14] = 0x77u;
  base[15] = 0x66u;
  base[16] = 0x55u;
  base[17] = 0x44u;
  base[18] = 0x33u;
  base[19] = 0x22u;
  base[20] = 0x11u;

  value = scalar_misalign_cross_ld(ptr);
  if (value != 0x1122334455667788ull) {
    return 11;
  }

  return 0;
}
