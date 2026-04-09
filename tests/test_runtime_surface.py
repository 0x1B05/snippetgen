from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]

RUNTIME_FILES = [
    "runtime/include/xsrt_env.h",
    "runtime/include/xsrt_csr.h",
    "runtime/include/xsrt_trap.h",
    "runtime/include/xsrt_intr.h",
    "runtime/src/xsrt_env.c",
    "runtime/src/xsrt_csr.c",
    "runtime/src/xsrt_trap.c",
    "runtime/src/xsrt_intr.c",
    "runtime/src/xsrt_snippet.c",
    "runtime/platform/xiangshan/xsrt_platform.h",
    "runtime/platform/xiangshan/xsrt_platform.c",
    "runtime/arch/riscv64/start.S",
    "runtime/arch/riscv64/trap.S",
    "snippets/include/xs_snippet.h",
]


class RuntimeSurfaceTest(unittest.TestCase):
    def test_runtime_files_exist(self) -> None:
        for relative_path in RUNTIME_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_runtime_headers_expose_minimal_api(self) -> None:
        env_h = (ROOT / "runtime/include/xsrt_env.h").read_text()
        csr_h = (ROOT / "runtime/include/xsrt_csr.h").read_text()
        trap_h = (ROOT / "runtime/include/xsrt_trap.h").read_text()
        intr_h = (ROOT / "runtime/include/xsrt_intr.h").read_text()
        snippet_h = (ROOT / "snippets/include/xs_snippet.h").read_text()

        self.assertIn("typedef struct {", env_h)
        self.assertIn("uint64_t hartid;", env_h)
        self.assertIn("uint64_t test_id;", env_h)
        self.assertIn("uint64_t snippet_id;", env_h)
        self.assertIn("uint64_t seed;", env_h)
        self.assertIn("uint64_t flags;", env_h)
        self.assertIn("void xsrt_init(xsrt_env_t *env);", env_h)
        self.assertIn("void xsrt_finish_pass(xsrt_env_t *env);", env_h)
        self.assertIn("void xsrt_finish_fail(xsrt_env_t *env, uint64_t code);", env_h)

        self.assertIn("uint64_t xsrt_csr_read(uint32_t csr);", csr_h)
        self.assertIn("void xsrt_csr_write(uint32_t csr, uint64_t val);", csr_h)

        self.assertIn("typedef struct xsrt_trap_frame xsrt_trap_frame_t;", trap_h)
        self.assertIn("typedef xsrt_trap_frame_t *(*xsrt_trap_handler_t)(xsrt_trap_frame_t *);", trap_h)
        self.assertIn("void xsrt_install_strap(xsrt_trap_handler_t fn);", trap_h)

        self.assertIn("void xsrt_enable_stimer(void);", intr_h)
        self.assertIn("void xsrt_timer_arm_delta(uint64_t cycles);", intr_h)

        self.assertIn("typedef struct {", snippet_h)
        self.assertIn("const char *id;", snippet_h)
        self.assertIn("int (*init)(xsrt_env_t *env);", snippet_h)
        self.assertIn("int (*run)(xsrt_env_t *env);", snippet_h)
        self.assertIn("int (*check)(xsrt_env_t *env);", snippet_h)
        self.assertIn("void (*fini)(xsrt_env_t *env);", snippet_h)
        self.assertIn("int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);", snippet_h)

    def test_runtime_c_surfaces_compile_and_runner_executes(self) -> None:
        smoke_c = textwrap.dedent(
            """
            #include <stdint.h>
            #include <stdio.h>

            #include "xsrt_env.h"
            #include "xsrt_csr.h"
            #include "xsrt_trap.h"
            #include "xsrt_intr.h"
            #include "xs_snippet.h"

            static int order[4];
            static int order_count = 0;

            static int mark_init(xsrt_env_t *env) {
              order[order_count++] = 1;
              env->test_id = 7;
              return 0;
            }

            static int mark_run(xsrt_env_t *env) {
              order[order_count++] = 2;
              xsrt_csr_write(5u, 99u);
              env->snippet_id = xsrt_csr_read(5u);
              return 0;
            }

            static int mark_check(xsrt_env_t *env) {
              order[order_count++] = 3;
              return env->snippet_id == 99u ? 0 : 11;
            }

            static void mark_fini(xsrt_env_t *env) {
              order[order_count++] = 4;
              env->flags |= 1u;
            }

            int main(void) {
              xsrt_env_t env;
              const xsrt_snippet_desc_t snippet = {
                .id = "smoke",
                .init = mark_init,
                .run = mark_run,
                .check = mark_check,
                .fini = mark_fini,
              };

              xsrt_init(&env);
              xsrt_install_strap(0);
              xsrt_enable_stimer();
              xsrt_timer_arm_delta(32u);

              if (xsrt_run_snippet(&env, &snippet) != 0) {
                return 21;
              }

              if (order_count != 4) {
                return 22;
              }

              for (int i = 0; i < 4; ++i) {
                if (order[i] != i + 1) {
                  return 23;
                }
              }

              if ((env.flags & 1u) == 0u || env.test_id != 7u || env.snippet_id != 99u) {
                return 24;
              }

              xsrt_finish_pass(&env);
              return 0;
            }
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            smoke_path = Path(tmpdir) / "runtime_smoke.c"
            binary_path = Path(tmpdir) / "runtime_smoke"
            smoke_path.write_text(smoke_c)

            compile_cmd = [
                "cc",
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(ROOT / "runtime/include"),
                "-I",
                str(ROOT / "snippets/include"),
                "-I",
                str(ROOT / "runtime/platform/xiangshan"),
                str(smoke_path),
                str(ROOT / "runtime/src/xsrt_env.c"),
                str(ROOT / "runtime/src/xsrt_csr.c"),
                str(ROOT / "runtime/src/xsrt_trap.c"),
                str(ROOT / "runtime/src/xsrt_intr.c"),
                str(ROOT / "runtime/src/xsrt_snippet.c"),
                str(ROOT / "runtime/platform/xiangshan/xsrt_platform.c"),
                "-o",
                str(binary_path),
            ]
            compile_result = subprocess.run(
                compile_cmd,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                compile_result.returncode,
                msg=compile_result.stderr,
            )

            run_result = subprocess.run(
                [str(binary_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, run_result.returncode, msg=run_result.stderr)


if __name__ == "__main__":
    unittest.main()
