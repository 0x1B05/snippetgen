#include <stdint.h>

static uint8_t scalar_misalign_store_load_overlap_arena[48] __attribute__((aligned(16)));

static void scalar_misalign_store_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
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
  uint8_t *base = &scalar_misalign_store_load_overlap_arena[0];
  uint8_t *store_ptr = base + 15u;
  const uint8_t *fragment_ptr = base + 16u;
  uint64_t value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_store_load_overlap_arena); ++index) {
    scalar_misalign_store_load_overlap_arena[index] = 0u;
  }

  scalar_misalign_store_sd(store_ptr, 0x1122334455667788ull);
  value = scalar_misalign_load_ld(store_ptr);
  if (value != 0x1122334455667788ull) {
    return 11;
  }

  if (fragment_ptr[0] != 0x77u || fragment_ptr[1] != 0x66u || fragment_ptr[2] != 0x55u ||
      fragment_ptr[3] != 0x44u || fragment_ptr[4] != 0x33u || fragment_ptr[5] != 0x22u ||
      fragment_ptr[6] != 0x11u) {
    return 12;
  }

  return 0;
}
