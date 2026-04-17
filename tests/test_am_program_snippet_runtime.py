from pathlib import Path
import importlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]

XSAM_RUNTIME_FILES = [
    "runtime/include/xsam/am.h",
    "runtime/include/xsam/amdev.h",
    "runtime/include/xsam/context.h",
    "runtime/include/xsam/vme.h",
    "runtime/include/xsam/ioe.h",
    "runtime/include/xsam/program_snippet.h",
    "runtime/src/xsam_trm.c",
    "runtime/src/xsam_cte.c",
    "runtime/src/xsam_vme.c",
    "runtime/src/xsam_ioe.c",
    "runtime/src/xsam_program_snippet.c",
]


class AMProgramSnippetRuntimeTest(unittest.TestCase):
    def test_xsam_runtime_files_exist(self) -> None:
        for relative_path in XSAM_RUNTIME_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_xsam_headers_expose_am_compatible_surface(self) -> None:
        am_h = (ROOT / "runtime/include/xsam/am.h").read_text()
        amdev_h = (ROOT / "runtime/include/xsam/amdev.h").read_text()
        context_h = (ROOT / "runtime/include/xsam/context.h").read_text()
        vme_h = (ROOT / "runtime/include/xsam/vme.h").read_text()
        ioe_h = (ROOT / "runtime/include/xsam/ioe.h").read_text()
        program_h = (ROOT / "runtime/include/xsam/program_snippet.h").read_text()

        self.assertIn("typedef struct xsam_context xsam_context_t;", am_h)
        self.assertIn("typedef struct xsam_address_space xsam_address_space_t;", am_h)
        self.assertIn("XSAM_EVENT_IRQ_TIMER", am_h)
        self.assertIn("XSAM_PROT_READ", am_h)
        self.assertIn("extern xsam_area_t xsam_heap;", am_h)
        self.assertIn("void xsam_putc(char ch);", am_h)
        self.assertIn("void xsam_halt(int code)", am_h)
        self.assertIn(
            "int xsam_cte_init(xsam_context_t *(*handler)(xsam_event_t event, xsam_context_t *ctx));",
            am_h,
        )
        self.assertIn("int xsam_vme_init(void *(*pgalloc)(size_t size), void (*pgfree)(void *));", am_h)
        self.assertIn("int xsam_ioe_init(void);", am_h)
        self.assertIn("int xsam_mpe_init(void (*entry)(void));", am_h)

        self.assertIn("#define XSAM_DEV_TIMER", amdev_h)
        self.assertIn("#define XSAM_DEV_SERIAL", amdev_h)
        self.assertIn("typedef struct { uint32_t hi, lo; } __attribute__((packed)) xsam_dev_timer_uptime_t;", amdev_h)
        self.assertIn("typedef struct { uint8_t data; } __attribute__((packed)) xsam_dev_serial_send_t;", amdev_h)

        self.assertIn("struct xsam_context {", context_h)
        self.assertIn("uintptr_t cause;", context_h)
        self.assertIn("uintptr_t epc;", context_h)

        self.assertIn("struct xsam_address_space {", vme_h)
        self.assertIn("size_t pgsize;", vme_h)
        self.assertIn("xsam_area_t area;", vme_h)
        self.assertIn("void *ptr;", vme_h)

        self.assertIn("size_t xsam_io_read(uint32_t dev, uintptr_t reg, void *buf, size_t size);", ioe_h)
        self.assertIn("size_t xsam_io_write(uint32_t dev, uintptr_t reg, const void *buf, size_t size);", ioe_h)

        self.assertIn("typedef int (*xsam_program_main_t)(void);", program_h)
        self.assertIn("xsrt_env_t *xsam_current_env(void);", program_h)
        self.assertIn("int xsam_run_program_main(xsrt_env_t *env, xsam_program_main_t entry);", program_h)
        self.assertIn("#define XSAM_DEFINE_PROGRAM_SNIPPET(symbol, snippet_id, entry_fn)", program_h)

    def test_xsam_sources_define_minimal_stateful_skeleton(self) -> None:
        trm_c = (ROOT / "runtime/src/xsam_trm.c").read_text()
        cte_c = (ROOT / "runtime/src/xsam_cte.c").read_text()
        vme_c = (ROOT / "runtime/src/xsam_vme.c").read_text()
        ioe_c = (ROOT / "runtime/src/xsam_ioe.c").read_text()
        program_c = (ROOT / "runtime/src/xsam_program_snippet.c").read_text()

        self.assertIn("xsam_area_t xsam_heap", trm_c)
        self.assertIn("void xsam_putc(char ch)", trm_c)
        self.assertIn("void xsam_halt(int code)", trm_c)
        self.assertIn("xsam_dev_serial_send_t payload", trm_c)
        self.assertIn("xsam_xs_serial_write(XSAM_DEVREG_SERIAL_SEND, &payload, sizeof(payload));", trm_c)

        self.assertIn("static xsam_context_t *(*g_event_handler)(xsam_event_t event, xsam_context_t *ctx);", cte_c)
        self.assertIn("int xsam_cte_init(xsam_context_t *(*handler)(xsam_event_t event, xsam_context_t *ctx))", cte_c)

        self.assertIn("static void *(*g_pgalloc)(size_t size);", vme_c)
        self.assertIn("static void (*g_pgfree)(void *ptr);", vme_c)
        self.assertIn("int xsam_vme_init(void *(*pgalloc)(size_t size), void (*pgfree)(void *))", vme_c)

        self.assertIn("int xsam_ioe_init(void)", ioe_c)
        self.assertIn("size_t xsam_io_read(uint32_t dev, uintptr_t reg, void *buf, size_t size)", ioe_c)
        self.assertIn("size_t xsam_io_write(uint32_t dev, uintptr_t reg, const void *buf, size_t size)", ioe_c)

        self.assertIn("static xsrt_env_t *g_program_env;", program_c)
        self.assertIn("xsrt_env_t *xsam_current_env(void)", program_c)
        self.assertIn("return entry();", program_c)

    def test_xsam_headers_and_sources_cross_compile(self) -> None:
        smoke_c = textwrap.dedent(
            """
            #include <stddef.h>
            #include <stdint.h>

            #include "xsam/am.h"
            #include "xsam/amdev.h"
            #include "xsam/context.h"
            #include "xsam/vme.h"
            #include "xsam/ioe.h"
            #include "xsam/program_snippet.h"

            static xsam_context_t *demo_handler(xsam_event_t event, xsam_context_t *ctx) {
              ctx->cause = event.cause;
              return ctx;
            }

            static int demo_main(void) {
              xsam_putc('A');
              return 0;
            }

            XSAM_DEFINE_PROGRAM_SNIPPET(snippet_demo_program, "demo_program", demo_main);

            int main(void) {
              xsam_address_space_t as = {0};
              xsam_dev_timer_uptime_t uptime = {0};
              xsam_dev_serial_send_t serial = {.data = 'B'};

              (void)as;
              (void)uptime;
              (void)serial;
              xsam_cte_init(demo_handler);
              xsam_intr_write(1);
              xsam_yield();
              return snippet_demo_program.id != 0;
            }
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            smoke_path = Path(tmpdir) / "xsam_smoke.c"
            object_path = Path(tmpdir) / "xsam_smoke.o"
            smoke_path.write_text(smoke_c)

            toolchain = importlib.import_module("generator.xsgen.toolchain")
            gcc = toolchain.detect_toolchain()["gcc"]
            compile_result = subprocess.run(
                [
                    gcc,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-O2",
                    "-march=rv64gcv_zicbop",
                    "-mabi=lp64d",
                    "-mcmodel=medany",
                    "-ffreestanding",
                    "-fno-asynchronous-unwind-tables",
                    "-fno-builtin",
                    "-fno-stack-protector",
                    "-fno-tree-vectorize",
                    "-fno-tree-slp-vectorize",
                    "-I",
                    str(ROOT / "runtime" / "include"),
                    "-I",
                    str(ROOT / "snippets" / "include"),
                    "-c",
                    str(smoke_path),
                    "-o",
                    str(object_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, compile_result.returncode, msg=compile_result.stderr)


if __name__ == "__main__":
    unittest.main()
