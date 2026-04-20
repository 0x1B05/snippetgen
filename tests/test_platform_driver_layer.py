from pathlib import Path
import json
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]

PLATFORM_DRIVER_FILES = [
    "runtime/platform/noop/xsam_noop_platform.h",
    "runtime/platform/noop/xsam_noop_clint.c",
    "runtime/platform/noop/xsam_noop_plic.c",
    "runtime/platform/noop/xsam_noop_serial.c",
    "runtime/platform/noop/xsam_noop_input.c",
    "runtime/platform/noop/xsam_noop_perf.c",
    "runtime/platform/xiangshan/xsam_xs_platform.h",
    "runtime/platform/xiangshan/xsam_xs_clint.c",
    "runtime/platform/xiangshan/xsam_xs_plic.c",
    "runtime/platform/xiangshan/xsam_xs_pma.c",
    "runtime/platform/xiangshan/xsam_xs_pmp.c",
    "runtime/platform/xiangshan/xsam_xs_cache.c",
]


class PlatformDriverLayerTest(unittest.TestCase):
    def test_platform_driver_files_exist(self) -> None:
        for relative_path in PLATFORM_DRIVER_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_timer_and_io_paths_use_platform_driver_helpers(self) -> None:
        intr_h = (ROOT / "runtime/include/xsrt_intr.h").read_text()
        trap_h = (ROOT / "runtime/include/xsrt_trap.h").read_text()
        platform_h = (ROOT / "runtime/platform/xiangshan/xsam_xs_platform.h").read_text()
        intr_c = (ROOT / "runtime/src/xsrt_intr.c").read_text()
        ioe_c = (ROOT / "runtime/src/xsam_ioe.c").read_text()
        pmp_c = (ROOT / "runtime/platform/xiangshan/xsam_xs_pmp.c").read_text()
        wait_c = (ROOT / "snippets/interrupt/interrupt_response_wait.c").read_text()

        self.assertIn("uint64_t xsrt_timer_read_uptime(void);", intr_h)
        self.assertIn("uint64_t xsrt_timer_read_compare(void);", intr_h)
        self.assertIn("uint64_t mtime_addr;", trap_h)
        self.assertIn("XSAM_XS_PMP_COUNT = 16u", platform_h)
        self.assertIn("XSAM_XS_PMP_R = 0x1", platform_h)
        self.assertIn("XSAM_XS_PMP_W = 0x2", platform_h)
        self.assertIn("XSAM_XS_PMP_X = 0x4", platform_h)
        self.assertIn("void xsam_xs_pmp_init(void);", platform_h)
        self.assertIn("uint64_t xsam_xs_pmp_read_num(int csr_num);", platform_h)
        self.assertIn("void xsam_xs_pmp_write_num(int csr_num, uint64_t value);", platform_h)
        self.assertIn("void xsam_xs_pmp_set_num(int csr_num, uint64_t value);", platform_h)
        self.assertIn("void xsam_xs_pmp_clear_num(int csr_num, uint64_t value);", platform_h)
        self.assertIn("void xsam_xs_pmp_enable_napot(", platform_h)
        self.assertIn("void xsam_xs_pmp_enable_tor(", platform_h)
        self.assertIn("void xsam_xs_pmp_disable(uintptr_t pmp_reg);", platform_h)

        self.assertIn('#include "xsam_xs_platform.h"', intr_c)
        self.assertIn("xsam_xs_clint_mtime_addr()", intr_c)
        self.assertIn("xsam_xs_clint_mtimecmp_addr()", intr_c)
        self.assertIn("xsam_xs_clint_read_mtime()", intr_c)
        self.assertIn("xsam_xs_clint_write_mtimecmp(", intr_c)
        self.assertNotIn("XSRT_CLINT_MTIMECMP_ADDR", intr_c)
        self.assertNotIn("XSRT_RTC_ADDR", intr_c)
        self.assertNotIn("XSRT_CLINT_MTIMECMP", intr_c)

        self.assertIn("case XSAM_DEV_TIMER:", ioe_c)
        self.assertIn("case XSAM_DEV_INPUT:", ioe_c)
        self.assertIn("case XSAM_DEV_SERIAL:", ioe_c)
        self.assertIn("case XSAM_DEV_PERFCNT:", ioe_c)
        self.assertIn("xsam_xs_clint_read_uptime", ioe_c)
        self.assertIn("xsam_xs_serial_write", ioe_c)
        self.assertIn("xsam_xs_pmp_init();", ioe_c)
        self.assertNotIn("0x3800bff8", ioe_c)

        self.assertIn("uint64_t xsam_xs_pmp_read_num(int csr_num)", pmp_c)
        self.assertIn("void xsam_xs_pmp_write_num(int csr_num, uint64_t value)", pmp_c)
        self.assertIn("void xsam_xs_pmp_set_num(int csr_num, uint64_t value)", pmp_c)
        self.assertIn("void xsam_xs_pmp_clear_num(int csr_num, uint64_t value)", pmp_c)
        self.assertIn("void xsam_xs_pmp_enable_napot(", pmp_c)
        self.assertIn("void xsam_xs_pmp_enable_tor(", pmp_c)
        self.assertIn("void xsam_xs_pmp_disable(uintptr_t pmp_reg)", pmp_c)
        self.assertIn("switch (csr_num)", pmp_c)
        self.assertIn("xsam_xs_pmp_write_num(XSAM_XS_PMPADDR_BASE + index, ~(uint64_t) 0u);", pmp_c)
        self.assertIn("xsam_xs_pmp_write_num(XSAM_XS_PMPCFG_BASE + 0u, 0u);", pmp_c)
        self.assertIn("xsam_xs_pmp_write_num(XSAM_XS_PMPCFG_BASE + 2u, 0u);", pmp_c)
        self.assertIn("xsam_xs_pmp_write_num(XSAM_XS_PMPADDR_BASE + pmp_reg, pmp_addr >> 2);", pmp_c)
        self.assertIn("xsam_xs_pmp_set_num(XSAM_XS_PMPCFG_BASE + cfg_offset, set_content << (cfg_shift * 8u));", pmp_c)

        self.assertIn("xsrt_timer_read_uptime()", wait_c)
        self.assertIn("xsrt_timer_read_compare()", wait_c)
        self.assertNotIn("XS_INTERRUPT_RTC_ADDR", wait_c)
        self.assertNotIn("XS_INTERRUPT_MTIMECMP_ADDR", wait_c)

    def test_build_manifest_includes_platform_driver_sources(self) -> None:
        build_dir = ROOT / "build" / "am_hello_main_poc"
        if build_dir.exists():
            import shutil

            shutil.rmtree(build_dir)

        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/am_hello_main_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        manifest = json.loads((build_dir / "build_manifest.json").read_text())
        compile_sources = [
            cmd[cmd.index("-c") + 1]
            for cmd in manifest["commands"]["compile"]
        ]

        self.assertIn(str((ROOT / "runtime" / "platform" / "xiangshan" / "xsam_xs_clint.c").resolve()), compile_sources)
        self.assertIn(str((ROOT / "runtime" / "platform" / "xiangshan" / "xsam_xs_plic.c").resolve()), compile_sources)
        self.assertIn(str((ROOT / "runtime" / "platform" / "xiangshan" / "xsam_xs_pma.c").resolve()), compile_sources)
        self.assertIn(str((ROOT / "runtime" / "platform" / "xiangshan" / "xsam_xs_pmp.c").resolve()), compile_sources)
        self.assertIn(str((ROOT / "runtime" / "platform" / "xiangshan" / "xsam_xs_cache.c").resolve()), compile_sources)


if __name__ == "__main__":
    unittest.main()
