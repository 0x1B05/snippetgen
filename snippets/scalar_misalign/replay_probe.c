#include <stdint.h>

#include "xs_scalar_misalign.h"
#include "xs_snippet.h"
#include "xsrt_csr.h"

static uint8_t xs_scalar_misalign_replay_arena[32768] __attribute__((aligned(64)));

static unsigned long xs_scalar_misalign_replay_skid(unsigned long lane, unsigned long count) {
  for (unsigned long index = 0; index < count; ++index) {
    __asm__ volatile(
        "addi %[lane], %[lane], 5\n"
        "xori %[lane], %[lane], 7\n"
        "andi %[lane], %[lane], 255\n"
        : [lane] "+r"(lane)
        :
        : "memory");
  }
  return lane;
}

static void xs_scalar_misalign_replay_write64(uint8_t *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %0, 0(%1)"
      :
      : "r"(value), "r"(ptr)
      : "memory");
}

static uint64_t xs_scalar_misalign_replay_load64(const uint8_t *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static void xs_scalar_misalign_replay_fill(uint8_t *base, uint64_t seed) {
  for (unsigned long index = 0; index < 16u; ++index) {
    xs_scalar_misalign_replay_write64(base + 64u * index, seed ^ (index << 12));
  }
}

static void xs_scalar_misalign_replay_zero_region(uint8_t *base) {
  *(uint64_t *) (base + 56u) = 0u;
  *(uint64_t *) (base + 64u) = 0u;
}

static int replay_probe_run(xsrt_env_t *env) {
  static const uint64_t kValue0 = 0x1122334455667788ull;
  static const uint64_t kValue1 = 0x2233445566778899ull;
  unsigned long rounds;
  unsigned long lane;

  if (env == 0) {
    return -1;
  }

  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE0, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE1, 0u);
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE2, 0u);

  rounds = 4u + (unsigned long) ((env->seed >> 16) & 0x3u);
  lane = (unsigned long) (env->seed | 1u);

  for (unsigned long round = 0; round < rounds; ++round) {
    uint8_t *slot = &xs_scalar_misalign_replay_arena[2048u * ((round + (unsigned long) (env->seed >> 24)) & 0xfu)];
    uint8_t *target_ptr = slot + 63u;
    uint8_t *fill_base = slot + 128u;
    uint64_t observed0;
    uint64_t observed1;

    xs_scalar_misalign_replay_zero_region(slot);
    xs_scalar_misalign_replay_fill(fill_base, (uint64_t) round << 32);
    lane = xs_scalar_misalign_replay_skid(lane, (env->seed & 0x7u) + (round & 0x3u));
    xs_scalar_misalign_replay_write64(target_ptr, kValue0 ^ round);
    observed0 = xs_scalar_misalign_replay_load64(target_ptr);
    lane = xs_scalar_misalign_replay_skid(lane, ((env->seed >> 3) & 0x7u) + 1u);
    xs_scalar_misalign_replay_fill(fill_base + 1024u, ((uint64_t) lane << 32) ^ round);
    xs_scalar_misalign_replay_write64(target_ptr, kValue1 ^ round);
    observed1 = xs_scalar_misalign_replay_load64(target_ptr);

    if (observed0 != (kValue0 ^ round) || observed1 != (kValue1 ^ round)) {
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_FAIL_CASE, 361u + round);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE0, observed0);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE1, observed1);
      xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_VALUE2, round);
      return XS_SCALAR_MISALIGN_RC_REPLAY_PROBE + (int) round;
    }
  }

  env->snippet_id = XS_SCALAR_MISALIGN_REPLAY_PROBE_MAGIC ^ (uint64_t) rounds;
  xsrt_csr_write(XS_SCALAR_MISALIGN_CSR_PROBE_COUNT, rounds);
  return 0;
}

const xsrt_snippet_desc_t snippet_replay_probe = {
  .id = "replay_probe",
  .run = replay_probe_run,
};
