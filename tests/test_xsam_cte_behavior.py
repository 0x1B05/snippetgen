from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class XSAMCTEBehaviorTest(unittest.TestCase):
    def test_cte_timer_trap_translates_into_am_event(self) -> None:
        harness_c = textwrap.dedent(
            """
            #include <stdint.h>
            #include <stdio.h>

            #include "xsam/am.h"
            #include "xsrt_env.h"
            #include "xsrt_trap.h"

            static xsrt_env_t g_env;
            static xsrt_trap_handler_t g_strap;
            static int g_cte_active;
            static int g_seen;
            static int g_last_event;
            static uintptr_t g_last_cause;
            static uintptr_t g_last_ref;

            void xsrt_install_strap(xsrt_trap_handler_t fn) {
              g_strap = fn;
            }

            void xsrt_timer_set_cte_active(int active) {
              g_cte_active = active;
            }

            xsrt_env_t *xsrt_current_env(void) {
              return &g_env;
            }

            static xsam_context_t *on_event(xsam_event_t event, xsam_context_t *ctx) {
              g_seen += 1;
              g_last_event = event.event;
              g_last_cause = event.cause;
              g_last_ref = event.ref;
              ctx->epc += 4u;
              return ctx;
            }

            int main(void) {
              xsrt_trap_frame_t frame = {
                .epc = 0x1000u,
                .cause = 0x8000000000000007ull,
                .tval = 0x55u,
              };

              if (xsam_cte_init(on_event) != 0) {
                return 11;
              }
              if (g_strap == 0 || g_cte_active == 0) {
                return 12;
              }

              g_strap(&frame);

              if (g_seen != 1 || g_last_event != XSAM_EVENT_IRQ_TIMER) {
                return 13;
              }
              if (g_last_cause != 0x8000000000000007ull || g_last_ref != 0x55u) {
                return 14;
              }
              if (frame.epc != 0x1004u) {
                return 15;
              }

              puts("ok");
              return 0;
            }
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            harness_path = Path(tmpdir) / "xsam_cte_host.c"
            exe_path = Path(tmpdir) / "xsam_cte_host"
            harness_path.write_text(harness_c)

            compile_result = subprocess.run(
                [
                    "cc",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(ROOT / "runtime" / "include"),
                    str(harness_path),
                    str(ROOT / "runtime" / "src" / "xsam_cte.c"),
                    "-o",
                    str(exe_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, compile_result.returncode, msg=compile_result.stderr)

            run_result = subprocess.run(
                [str(exe_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, run_result.returncode, msg=run_result.stderr)
            self.assertIn("ok", run_result.stdout)

    def test_cte_sources_hook_into_timer_trap_dispatch(self) -> None:
        cte_c = (ROOT / "runtime/src/xsam_cte.c").read_text()
        trap_s = (ROOT / "runtime/arch/riscv64/trap.S").read_text()
        intr_h = (ROOT / "runtime/include/xsrt_intr.h").read_text()
        intr_c = (ROOT / "runtime/src/xsrt_intr.c").read_text()

        self.assertIn("static xsrt_trap_frame_t *xsam_cte_trap_handler(xsrt_trap_frame_t *frame)", cte_c)
        self.assertIn("xsrt_install_strap(xsam_cte_trap_handler);", cte_c)
        self.assertIn("xsrt_timer_set_cte_active(handler != 0);", cte_c)
        self.assertIn("XSAM_EVENT_IRQ_TIMER", cte_c)

        self.assertIn("void xsrt_timer_set_cte_active(int active);", intr_h)
        self.assertIn("static void xsrt_install_timer_trap_state(void)", intr_c)
        self.assertIn("if (g_stimer_enabled != 0)", intr_c)
        self.assertIn('csrw mscratch, %0', intr_c)
        self.assertIn("xsrt_install_timer_trap_state();", intr_c)
        self.assertIn("XSRT_TIMER_STATE_CTE_ACTIVE", trap_s)
        self.assertIn("bnez a1, xsrt_trap_entry_generic_restore", trap_s)

    def test_cte_maps_yield_syscall_and_pagefault_events(self) -> None:
        harness_c = textwrap.dedent(
            """
            #include <stdint.h>
            #include <stdio.h>

            #include "xsam/am.h"
            #include "xsrt_env.h"
            #include "xsrt_trap.h"

            static xsrt_trap_handler_t g_strap;
            static int g_events[3];
            static int g_event_count;

            void xsrt_install_strap(xsrt_trap_handler_t fn) {
              g_strap = fn;
            }

            void xsrt_timer_set_cte_active(int active) {
              (void) active;
            }

            xsrt_env_t *xsrt_current_env(void) {
              return 0;
            }

            static xsam_context_t *on_event(xsam_event_t event, xsam_context_t *ctx) {
              g_events[g_event_count++] = event.event;
              return ctx;
            }

            int main(void) {
              xsrt_trap_frame_t yield_frame = {
                .epc = 0x10u,
                .cause = 11u,
              };
              xsrt_trap_frame_t syscall_frame = {
                .epc = 0x20u,
                .cause = 11u,
              };
              xsrt_trap_frame_t pagefault_frame = {
                .epc = 0x30u,
                .cause = 13u,
                .tval = 0xdeadbeefu,
              };

              yield_frame.gpr[17] = (uint64_t) -1ll;
              syscall_frame.gpr[17] = 0u;

              if (xsam_cte_init(on_event) != 0 || g_strap == 0) {
                return 21;
              }

              g_strap(&yield_frame);
              g_strap(&syscall_frame);
              g_strap(&pagefault_frame);

              if (g_event_count != 3) {
                return 22;
              }
              if (g_events[0] != XSAM_EVENT_YIELD) {
                return 23;
              }
              if (g_events[1] != XSAM_EVENT_SYSCALL) {
                return 24;
              }
              if (g_events[2] != XSAM_EVENT_PAGEFAULT) {
                return 25;
              }

              puts("ok");
              return 0;
            }
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            harness_path = Path(tmpdir) / "xsam_cte_events_host.c"
            exe_path = Path(tmpdir) / "xsam_cte_events_host"
            harness_path.write_text(harness_c)

            compile_result = subprocess.run(
                [
                    "cc",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(ROOT / "runtime" / "include"),
                    str(harness_path),
                    str(ROOT / "runtime" / "src" / "xsam_cte.c"),
                    "-o",
                    str(exe_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, compile_result.returncode, msg=compile_result.stderr)

            run_result = subprocess.run(
                [str(exe_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, run_result.returncode, msg=run_result.stderr)
            self.assertIn("ok", run_result.stdout)


if __name__ == "__main__":
    unittest.main()
