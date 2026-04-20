#include <stdint.h>

static uint8_t scalar_misalign_store_cross_16b_arena[64] __attribute__((aligned(16)));

static void scalar_misalign_store_sw(void *ptr, uint32_t value) {
  __asm__ volatile(
      "sw %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static void scalar_misalign_store_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

int main(void) {
  uint8_t *region_a = &scalar_misalign_store_cross_16b_arena[0];
  uint8_t *region_b = &scalar_misalign_store_cross_16b_arena[32];
  uint8_t *sd_ptr = region_a + 15u;
  uint8_t *sw_ptr = region_b + 14u;

  for (unsigned index = 0; index < sizeof(scalar_misalign_store_cross_16b_arena); ++index) {
    scalar_misalign_store_cross_16b_arena[index] = 0u;
  }

  scalar_misalign_store_sd(sd_ptr, 0x1122334455667788ull);
  if (sd_ptr[0] != 0x88u || sd_ptr[1] != 0x77u || sd_ptr[2] != 0x66u || sd_ptr[3] != 0x55u ||
      sd_ptr[4] != 0x44u || sd_ptr[5] != 0x33u || sd_ptr[6] != 0x22u || sd_ptr[7] != 0x11u) {
    return 11;
  }

  scalar_misalign_store_sw(sw_ptr, 0xaabbccddu);
  if (sw_ptr[0] != 0xddu || sw_ptr[1] != 0xccu || sw_ptr[2] != 0xbbu || sw_ptr[3] != 0xaau) {
    return 12;
  }

  return 0;
}
