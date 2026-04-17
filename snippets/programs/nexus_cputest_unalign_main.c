#include <stdint.h>

/*
 * Ported from nexus-am/tests/cputest/tests/unalign.c
 */

volatile unsigned nexus_cputest_unalign_x = 0xffffffffu;
volatile unsigned char nexus_cputest_unalign_buf[16];

int main(void) {
  for (int i = 0; i < 4; ++i) {
    *((volatile unsigned *) (nexus_cputest_unalign_buf + 3)) = 0xaabbccddu;

    nexus_cputest_unalign_x = *((volatile unsigned *) (nexus_cputest_unalign_buf + 3));
    if (nexus_cputest_unalign_x != 0xaabbccddu) {
      return 11 + i;
    }

    nexus_cputest_unalign_buf[0] = 0u;
    nexus_cputest_unalign_buf[1] = 0u;
  }

  return 0;
}
