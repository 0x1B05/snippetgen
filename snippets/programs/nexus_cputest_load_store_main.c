#include <stdint.h>

/*
 * Ported from nexus-am/tests/cputest/tests/load-store.c
 */

static unsigned short nexus_cputest_mem[] = {
    0x0000u, 0x0258u, 0x4abcu, 0x7fffu, 0x8000u, 0x8100u, 0xabcdu, 0xffffu,
};

static const unsigned nexus_cputest_lh_ans[] = {
    0x00000000u, 0x00000258u, 0x00004abcu, 0x00007fffu,
    0xffff8000u, 0xffff8100u, 0xffffabcdu, 0xffffffffu,
};

static const unsigned nexus_cputest_lhu_ans[] = {
    0x00000000u, 0x00000258u, 0x00004abcu, 0x00007fffu,
    0x00008000u, 0x00008100u, 0x0000abcdu, 0x0000ffffu,
};

static const unsigned nexus_cputest_sh_ans[] = {
    0x0000fffdu, 0x0000fff7u, 0x0000ffdFu, 0x0000ff7fu,
    0x0000fdffu, 0x0000f7ffu, 0x0000dfffu, 0x00007fffu,
};

static const unsigned nexus_cputest_lwlr_ans[] = {
    0xbc025800u, 0x007fff4au, 0xcd810080u, 0x00ffffabu,
};

int main(void) {
  unsigned i;

  for (i = 0; i < (sizeof(nexus_cputest_mem) / sizeof(nexus_cputest_mem[0])); ++i) {
    if ((short) nexus_cputest_mem[i] != (short) nexus_cputest_lh_ans[i]) {
      return 11 + (int) i;
    }
  }

  for (i = 0; i < (sizeof(nexus_cputest_mem) / sizeof(nexus_cputest_mem[0])); ++i) {
    if (nexus_cputest_mem[i] != nexus_cputest_lhu_ans[i]) {
      return 31 + (int) i;
    }
  }

  for (i = 0; i < ((sizeof(nexus_cputest_mem) / sizeof(nexus_cputest_mem[0])) / 2u) - 1u; ++i) {
    unsigned x = ((unsigned *) ((void *) nexus_cputest_mem + 1))[i];
    if (x != nexus_cputest_lwlr_ans[i]) {
      return 51 + (int) i;
    }
  }

  for (i = 0; i < (sizeof(nexus_cputest_mem) / sizeof(nexus_cputest_mem[0])); ++i) {
    nexus_cputest_mem[i] = (unsigned short) ~(1u << (2u * i + 1u));
    if (nexus_cputest_mem[i] != nexus_cputest_sh_ans[i]) {
      return 71 + (int) i;
    }
  }

  return 0;
}
