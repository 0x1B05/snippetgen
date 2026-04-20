from pathlib import Path
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class BuildPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.build_dir = ROOT / "build" / "scalar_load_legality_poc"
        self.vsetvl_build_dir = ROOT / "build" / "vsetvl_interrupt_path_poc"
        self.vsetvl_search_build_dir = ROOT / "build" / "vsetvl_interrupt_search_poc"
        self.interrupt_build_dir = ROOT / "build" / "interrupt_response_poc"
        self.split_store_build_dir = ROOT / "build" / "misaligned_split_store_search_poc"
        self.demo_build_dir = ROOT / "build" / "demo_mark_flag_poc"
        self.prefetchw_build_dir = ROOT / "build" / "prefetchw_tl_denied_fault_poc"
        self.am_program_build_dir = ROOT / "build" / "am_hello_main_poc"
        self.am_timer_program_build_dir = ROOT / "build" / "am_timer_event_poc"
        self.scalar_misalign_load_in_16b_build_dir = ROOT / "build" / "scalar_misalign_load_in_16b_poc"
        self.scalar_misalign_load_cross_16b_build_dir = ROOT / "build" / "scalar_misalign_load_cross_16b_poc"
        self.scalar_misalign_store_in_16b_build_dir = ROOT / "build" / "scalar_misalign_store_in_16b_poc"
        self.scalar_misalign_store_cross_16b_build_dir = ROOT / "build" / "scalar_misalign_store_cross_16b_poc"
        self.scalar_misalign_store_load_overlap_build_dir = ROOT / "build" / "scalar_misalign_store_load_overlap_poc"
        self.scalar_misalign_load_split_build_dir = ROOT / "build" / "scalar_misalign_load_split_templates_poc"
        self.scalar_misalign_store_split_build_dir = ROOT / "build" / "scalar_misalign_store_split_templates_poc"
        self.scalar_misalign_cross_page_build_dir = ROOT / "build" / "scalar_misalign_cross_page_faults_poc"
        self.scalar_misalign_store_forward_overlap_build_dir = ROOT / "build" / "scalar_misalign_store_forward_overlap_poc"
        self.scalar_misalign_store_forward_search_build_dir = ROOT / "build" / "scalar_misalign_store_forward_search_poc"
        self.scalar_misalign_cross_page_search_build_dir = ROOT / "build" / "scalar_misalign_cross_page_fault_search_poc"
        self.scalar_misalign_replay_probe_build_dir = ROOT / "build" / "scalar_misalign_replay_probe_poc"
        self.nexus_cputest_unalign_build_dir = ROOT / "build" / "nexus_cputest_unalign_poc"
        self.nexus_cputest_load_store_build_dir = ROOT / "build" / "nexus_cputest_load_store_poc"
        self.nexus_memscan_access_fault_build_dir = ROOT / "build" / "nexus_memscan_access_fault_poc"
        self.nexus_memscan_fetch_fault_build_dir = ROOT / "build" / "nexus_memscan_fetch_fault_poc"
        self.nexus_memscan_hugepage_access_fault_build_dir = ROOT / "build" / "nexus_memscan_hugepage_access_fault_poc"
        self.nexus_memscan_hugepage_atom_fault_build_dir = ROOT / "build" / "nexus_memscan_hugepage_atom_fault_poc"
        self.nexus_memscan_hugepage_build_dir = ROOT / "build" / "nexus_memscan_hugepage_poc"
        self.nexus_memscan_page_fault_build_dir = ROOT / "build" / "nexus_memscan_page_fault_poc"
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.vsetvl_build_dir.exists():
            shutil.rmtree(self.vsetvl_build_dir)
        if self.vsetvl_search_build_dir.exists():
            shutil.rmtree(self.vsetvl_search_build_dir)
        if self.interrupt_build_dir.exists():
            shutil.rmtree(self.interrupt_build_dir)
        if self.split_store_build_dir.exists():
            shutil.rmtree(self.split_store_build_dir)
        if self.demo_build_dir.exists():
            shutil.rmtree(self.demo_build_dir)
        if self.prefetchw_build_dir.exists():
            shutil.rmtree(self.prefetchw_build_dir)
        if self.am_program_build_dir.exists():
            shutil.rmtree(self.am_program_build_dir)
        if self.am_timer_program_build_dir.exists():
            shutil.rmtree(self.am_timer_program_build_dir)
        if self.scalar_misalign_load_in_16b_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_load_in_16b_build_dir)
        if self.scalar_misalign_load_cross_16b_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_load_cross_16b_build_dir)
        if self.scalar_misalign_store_in_16b_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_in_16b_build_dir)
        if self.scalar_misalign_store_cross_16b_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_cross_16b_build_dir)
        if self.scalar_misalign_store_load_overlap_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_load_overlap_build_dir)
        if self.scalar_misalign_load_split_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_load_split_build_dir)
        if self.scalar_misalign_store_split_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_split_build_dir)
        if self.scalar_misalign_cross_page_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_cross_page_build_dir)
        if self.scalar_misalign_store_forward_overlap_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_forward_overlap_build_dir)
        if self.scalar_misalign_store_forward_search_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_store_forward_search_build_dir)
        if self.scalar_misalign_cross_page_search_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_cross_page_search_build_dir)
        if self.scalar_misalign_replay_probe_build_dir.exists():
            shutil.rmtree(self.scalar_misalign_replay_probe_build_dir)
        if self.nexus_cputest_unalign_build_dir.exists():
            shutil.rmtree(self.nexus_cputest_unalign_build_dir)
        if self.nexus_cputest_load_store_build_dir.exists():
            shutil.rmtree(self.nexus_cputest_load_store_build_dir)
        if self.nexus_memscan_access_fault_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_access_fault_build_dir)
        if self.nexus_memscan_fetch_fault_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_fetch_fault_build_dir)
        if self.nexus_memscan_hugepage_access_fault_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_hugepage_access_fault_build_dir)
        if self.nexus_memscan_hugepage_atom_fault_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_hugepage_atom_fault_build_dir)
        if self.nexus_memscan_hugepage_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_hugepage_build_dir)
        if self.nexus_memscan_page_fault_build_dir.exists():
            shutil.rmtree(self.nexus_memscan_page_fault_build_dir)

    def test_emitter_generates_harness_in_suite_order(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/scalar_load_legality_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)

        harness = artifact.generated_suite_path.read_text()
        ordered_symbols = [
            "snippet_init_basic_env",
            "snippet_arm_timer",
            "snippet_unaligned_load",
            "snippet_check_scalar_load_legality",
            "snippet_finish_check",
        ]
        last_index = -1
        for symbol in ordered_symbols:
            current_index = harness.index(symbol)
            self.assertGreater(current_index, last_index)
            last_index = current_index
        self.assertIn("env.seed = 0x1234ull;", harness)

    def test_suite_reorder_changes_generated_harness_order(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_suite = Path(tmpdir) / "reordered.yaml"
            tmp_suite.write_text(
                textwrap.dedent(
                    """
                    suite: reordered
                    target: xiangshan-verilator
                    seed: 99
                    compose:
                      mode: sequence
                      snippets:
                        - finish_check
                        - unaligned_load
                        - init_basic_env
                    """
                ).strip()
            )
            suite = suite_loader.load_suite(tmp_suite)
            plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
            artifact = toolchain.artifact_paths_for_suite(Path(tmpdir), suite.name)
            emitter.emit_harness(plan, artifact.generated_suite_path)
            harness = artifact.generated_suite_path.read_text()

            finish_idx = harness.index("snippet_finish_check")
            unaligned_idx = harness.index("snippet_unaligned_load")
            init_idx = harness.index("snippet_init_basic_env")
            self.assertLess(finish_idx, unaligned_idx)
            self.assertLess(unaligned_idx, init_idx)

    def test_emitter_propagates_non_default_suite_seed(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_suite = Path(tmpdir) / "seeded.yaml"
            tmp_suite.write_text(
                textwrap.dedent(
                    """
                    suite: seeded
                    target: xiangshan-verilator
                    seed: 99
                    compose:
                      mode: sequence
                      snippets:
                        - init_basic_env
                    """
                ).strip()
            )
            suite = suite_loader.load_suite(tmp_suite)
            plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
            artifact = toolchain.artifact_paths_for_suite(Path(tmpdir), suite.name)
            emitter.emit_harness(plan, artifact.generated_suite_path)
            harness = artifact.generated_suite_path.read_text()

            self.assertIn("xsrt_init(&env);", harness)
            self.assertIn("env.seed = 0x63ull;", harness)
            self.assertLess(harness.index("xsrt_init(&env);"), harness.index("env.seed = 0x63ull;"))
            self.assertLess(harness.index("env.seed = 0x63ull;"), harness.index("xsrt_run_snippet(&env, &snippet_init_basic_env);"))

    def test_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/scalar_load_legality_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.build_dir / "generated_suite.c"
        test_elf = self.build_dir / "test.elf"
        test_bin = self.build_dir / "test.bin"
        disasm = self.build_dir / "disasm"
        build_manifest = self.build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("scalar_load_legality_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "arm_timer", "unaligned_load", "check_scalar_load_legality", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])
        self.assertTrue(manifest["commands"]["compile"])
        self.assertTrue(manifest["commands"]["link"])
        self.assertTrue(manifest["commands"]["objcopy"])

    def test_vsetvl_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/vsetvl_interrupt_path_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.vsetvl_build_dir / "generated_suite.c"
        test_elf = self.vsetvl_build_dir / "test.elf"
        test_bin = self.vsetvl_build_dir / "test.bin"
        disasm = self.vsetvl_build_dir / "disasm"
        build_manifest = self.vsetvl_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("vsetvl_interrupt_path_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "arm_timer", "vsetvl_interrupt_path", "check_vsetvl_interrupt_path", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])
        self.assertTrue(manifest["commands"]["compile"])
        self.assertTrue(manifest["commands"]["link"])
        self.assertTrue(manifest["commands"]["objcopy"])

    def test_interrupt_response_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/interrupt_response_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.interrupt_build_dir / "generated_suite.c"
        test_elf = self.interrupt_build_dir / "test.elf"
        test_bin = self.interrupt_build_dir / "test.bin"
        disasm = self.interrupt_build_dir / "disasm"
        build_manifest = self.interrupt_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("interrupt_response_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "arm_timer", "interrupt_response_wait", "check_interrupt_response", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])

    def test_vsetvl_search_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/vsetvl_interrupt_search_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.vsetvl_search_build_dir / "generated_suite.c"
        test_elf = self.vsetvl_search_build_dir / "test.elf"
        test_bin = self.vsetvl_search_build_dir / "test.bin"
        disasm = self.vsetvl_search_build_dir / "disasm"
        build_manifest = self.vsetvl_search_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("vsetvl_interrupt_search_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "vsetvl_interrupt_search", "check_vsetvl_interrupt_search", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])

    def test_split_store_search_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/misaligned_split_store_search_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.split_store_build_dir / "generated_suite.c"
        test_elf = self.split_store_build_dir / "test.elf"
        test_bin = self.split_store_build_dir / "test.bin"
        disasm = self.split_store_build_dir / "disasm"
        build_manifest = self.split_store_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("misaligned_split_store_search_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "misaligned_split_store_search", "check_misaligned_split_store_search", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])

    def test_demo_mark_flag_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/demo_mark_flag_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.demo_build_dir / "generated_suite.c"
        test_elf = self.demo_build_dir / "test.elf"
        test_bin = self.demo_build_dir / "test.bin"
        disasm = self.demo_build_dir / "disasm"
        build_manifest = self.demo_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("demo_mark_flag_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "demo_mark_flag", "check_demo_mark_flag", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])

    def test_am_program_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/am_hello_main_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.am_program_build_dir / "generated_suite.c"
        test_elf = self.am_program_build_dir / "test.elf"
        test_bin = self.am_program_build_dir / "test.bin"
        disasm = self.am_program_build_dir / "disasm"
        build_manifest = self.am_program_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("am_hello_main_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "am_hello_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])

        generated_text = generated_suite.read_text()
        self.assertIn('#include "xsam/program_snippet.h"', generated_text)
        self.assertIn("xsam_program_entry_am_hello_main", generated_text)

        compile_sources = [
            cmd[cmd.index("-c") + 1]
            for cmd in manifest["commands"]["compile"]
        ]
        self.assertNotIn(str((ROOT / "snippets" / "programs" / "am_hello_main.c").resolve()), compile_sources)
        self.assertIn(str(generated_suite), compile_sources)
        self.assertIn(str((ROOT / "runtime" / "src" / "xsam_program_snippet.c").resolve()), compile_sources)

    def test_am_timer_program_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/am_timer_event_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.am_timer_program_build_dir / "generated_suite.c"
        test_elf = self.am_timer_program_build_dir / "test.elf"
        test_bin = self.am_timer_program_build_dir / "test.bin"
        disasm = self.am_timer_program_build_dir / "disasm"
        build_manifest = self.am_timer_program_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("am_timer_event_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "arm_timer", "am_timer_event_main", "check_interrupt_response", "finish_check"],
            manifest["snippet_ids"],
        )

        generated_text = generated_suite.read_text()
        self.assertIn("snippet_arm_timer", generated_text)
        self.assertIn("snippet_am_timer_event_main", generated_text)
        self.assertIn("snippet_check_interrupt_response", generated_text)
        self.assertIn("xsam_program_entry_am_timer_event_main", generated_text)

    def test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_cputest_unalign_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_cputest_unalign_build_dir / "generated_suite.c"
        build_manifest = self.nexus_cputest_unalign_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_cputest_unalign_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_cputest_unalign_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_cputest_unalign_main", generated_suite.read_text())

    def assert_am_program_suite_build(
        self,
        *,
        suite_path: str,
        build_dir: Path,
        suite_name: str,
        snippet_id: str,
    ) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", suite_path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = build_dir / "generated_suite.c"
        build_manifest = build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual(suite_name, manifest["suite"])
        self.assertEqual(
            ["init_basic_env", snippet_id, "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn(f"xsam_program_entry_{snippet_id}", generated_suite.read_text())

    def test_scalar_misalign_load_in_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_am_program_suite_build(
            suite_path="suites/scalar_misalign_load_in_16b_poc.yaml",
            build_dir=self.scalar_misalign_load_in_16b_build_dir,
            suite_name="scalar_misalign_load_in_16b_poc",
            snippet_id="scalar_misalign_load_in_16b_main",
        )

    def test_scalar_misalign_load_cross_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_am_program_suite_build(
            suite_path="suites/scalar_misalign_load_cross_16b_poc.yaml",
            build_dir=self.scalar_misalign_load_cross_16b_build_dir,
            suite_name="scalar_misalign_load_cross_16b_poc",
            snippet_id="scalar_misalign_load_cross_16b_main",
        )

    def test_scalar_misalign_store_in_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_am_program_suite_build(
            suite_path="suites/scalar_misalign_store_in_16b_poc.yaml",
            build_dir=self.scalar_misalign_store_in_16b_build_dir,
            suite_name="scalar_misalign_store_in_16b_poc",
            snippet_id="scalar_misalign_store_in_16b_main",
        )

    def test_scalar_misalign_store_cross_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_am_program_suite_build(
            suite_path="suites/scalar_misalign_store_cross_16b_poc.yaml",
            build_dir=self.scalar_misalign_store_cross_16b_build_dir,
            suite_name="scalar_misalign_store_cross_16b_poc",
            snippet_id="scalar_misalign_store_cross_16b_main",
        )

    def test_scalar_misalign_store_load_overlap_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_am_program_suite_build(
            suite_path="suites/scalar_misalign_store_load_overlap_poc.yaml",
            build_dir=self.scalar_misalign_store_load_overlap_build_dir,
            suite_name="scalar_misalign_store_load_overlap_poc",
            snippet_id="scalar_misalign_store_load_overlap_main",
        )

    def assert_proc_check_suite_build(
        self,
        *,
        suite_path: str,
        build_dir: Path,
        suite_name: str,
        snippet_ids: list[str],
    ) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", suite_path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = build_dir / "generated_suite.c"
        build_manifest = build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual(suite_name, manifest["suite"])
        self.assertEqual(snippet_ids, manifest["snippet_ids"])

        generated_text = generated_suite.read_text()
        for snippet_id in snippet_ids:
            self.assertIn(f"snippet_{snippet_id}", generated_text)

    def test_scalar_misalign_load_split_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_load_split_templates_poc.yaml",
            build_dir=self.scalar_misalign_load_split_build_dir,
            suite_name="scalar_misalign_load_split_templates_poc",
            snippet_ids=[
                "init_basic_env",
                "load_split_templates",
                "check_load_split_templates",
                "finish_check",
            ],
        )

    def test_scalar_misalign_store_split_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_store_split_templates_poc.yaml",
            build_dir=self.scalar_misalign_store_split_build_dir,
            suite_name="scalar_misalign_store_split_templates_poc",
            snippet_ids=[
                "init_basic_env",
                "store_split_templates",
                "check_store_split_templates",
                "finish_check",
            ],
        )

    def test_scalar_misalign_cross_page_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_cross_page_faults_poc.yaml",
            build_dir=self.scalar_misalign_cross_page_build_dir,
            suite_name="scalar_misalign_cross_page_faults_poc",
            snippet_ids=[
                "init_basic_env",
                "cross_page_faults",
                "check_cross_page_faults",
                "finish_check",
            ],
        )

    def test_scalar_misalign_store_forward_overlap_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_store_forward_overlap_poc.yaml",
            build_dir=self.scalar_misalign_store_forward_overlap_build_dir,
            suite_name="scalar_misalign_store_forward_overlap_poc",
            snippet_ids=[
                "init_basic_env",
                "store_forward_overlap",
                "check_store_forward_overlap",
                "finish_check",
            ],
        )

    def test_scalar_misalign_store_forward_search_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_store_forward_search_poc.yaml",
            build_dir=self.scalar_misalign_store_forward_search_build_dir,
            suite_name="scalar_misalign_store_forward_search_poc",
            snippet_ids=[
                "init_basic_env",
                "store_forward_search",
                "check_store_forward_search",
                "finish_check",
            ],
        )

    def test_scalar_misalign_cross_page_fault_search_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_cross_page_fault_search_poc.yaml",
            build_dir=self.scalar_misalign_cross_page_search_build_dir,
            suite_name="scalar_misalign_cross_page_fault_search_poc",
            snippet_ids=[
                "init_basic_env",
                "cross_page_fault_search",
                "check_cross_page_fault_search",
                "finish_check",
            ],
        )

    def test_scalar_misalign_replay_probe_suite_build_generates_artifacts_and_manifest(self) -> None:
        self.assert_proc_check_suite_build(
            suite_path="suites/scalar_misalign_replay_probe_poc.yaml",
            build_dir=self.scalar_misalign_replay_probe_build_dir,
            suite_name="scalar_misalign_replay_probe_poc",
            snippet_ids=[
                "init_basic_env",
                "replay_probe",
                "check_replay_probe",
                "finish_check",
            ],
        )

    def test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_cputest_load_store_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_cputest_load_store_build_dir / "generated_suite.c"
        build_manifest = self.nexus_cputest_load_store_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_cputest_load_store_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_cputest_load_store_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_cputest_load_store_main", generated_suite.read_text())

    def test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_access_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_access_fault_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_access_fault_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_access_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_access_fault_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_access_fault_main", generated_suite.read_text())

    def test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_fetch_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_fetch_fault_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_fetch_fault_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_fetch_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_fetch_fault_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_fetch_fault_main", generated_suite.read_text())

    def test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_hugepage_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_hugepage_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_hugepage_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_hugepage_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_hugepage_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_hugepage_main", generated_suite.read_text())

    def test_nexus_memscan_hugepage_access_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_hugepage_access_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_hugepage_access_fault_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_hugepage_access_fault_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_hugepage_access_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_hugepage_access_fault_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_hugepage_access_fault_main", generated_suite.read_text())

    def test_nexus_memscan_hugepage_atom_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_hugepage_atom_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_hugepage_atom_fault_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_hugepage_atom_fault_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_hugepage_atom_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_hugepage_atom_fault_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_hugepage_atom_fault_main", generated_suite.read_text())

    def test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/nexus_memscan_page_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.nexus_memscan_page_fault_build_dir / "generated_suite.c"
        build_manifest = self.nexus_memscan_page_fault_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("nexus_memscan_page_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "nexus_memscan_page_fault_main", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertIn("xsam_program_entry_nexus_memscan_page_fault_main", generated_suite.read_text())

    def test_vsetvl_suite_harness_order_and_final_elf_contains_vsetvl(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/vsetvl_interrupt_path_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)

        harness = artifact.generated_suite_path.read_text()
        ordered_symbols = [
            "snippet_init_basic_env",
            "snippet_arm_timer",
            "snippet_vsetvl_interrupt_path",
            "snippet_check_vsetvl_interrupt_path",
            "snippet_finish_check",
        ]
        last_index = -1
        for symbol in ordered_symbols:
            current_index = harness.index(symbol)
            self.assertGreater(current_index, last_index)
            last_index = current_index

        toolchain.build_artifacts(ROOT, plan, artifact)
        objdump = toolchain.resolve_objdump(toolchain.detect_toolchain())
        start_result = subprocess.run(
            [objdump, "-d", "--disassemble=_start", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, start_result.returncode, msg=start_result.stderr)
        self.assertIn("csrs\tmstatus,", start_result.stdout)

        loop_result = subprocess.run(
            [objdump, "-d", "--disassemble=vsetvl_interrupt_path_run", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, loop_result.returncode, msg=loop_result.stderr)
        self.assertIn("vsetvl\tzero,zero,zero", loop_result.stdout)

    def test_runtime_entry_emits_noop_halt_trap_after_main_returns(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/vsetvl_interrupt_path_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)

        objdump = toolchain.resolve_objdump(toolchain.detect_toolchain())
        disasm_result = subprocess.run(
            [objdump, "-d", "--disassemble=_start", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, disasm_result.returncode, msg=disasm_result.stderr)

        instructions = []
        for line in disasm_result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) < 3:
                continue
            instructions.append("\t".join(field.strip() for field in fields[2:] if field.strip()))

        call_index = next(
            index for index, instruction in enumerate(instructions)
            if instruction.startswith("call\t") or instruction.startswith("jal\t")
        )
        halt_index = next(
            index for index, instruction in enumerate(instructions)
            if instruction == ".word\t0x0005006b"
        )
        self.assertLess(call_index, halt_index)

    def test_interrupt_runtime_emits_trap_entry_and_timer_enable_sequence(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/interrupt_response_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)

        objdump = toolchain.resolve_objdump(toolchain.detect_toolchain())
        trap_result = subprocess.run(
            [objdump, "-d", "--disassemble=xsrt_trap_entry", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, trap_result.returncode, msg=trap_result.stderr)
        self.assertIn("mret", trap_result.stdout)
        self.assertIn("csrrw", trap_result.stdout)
        self.assertIn("mscratch", trap_result.stdout)

        arm_result = subprocess.run(
            [objdump, "-d", "--disassemble=xsrt_enable_stimer", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, arm_result.returncode, msg=arm_result.stderr)
        instructions = []
        for line in arm_result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) < 3:
                continue
            instructions.append("\t".join(field.strip() for field in fields[2:] if field.strip()))

        self.assertTrue(any(instruction.startswith("csrw\tmtvec,") for instruction in instructions))
        self.assertTrue(any(instruction.startswith("csrw\tmscratch,") for instruction in instructions))
        self.assertTrue(any(instruction.startswith("csrs\tmie,") for instruction in instructions))
        self.assertTrue(any(instruction.startswith("csrs\tmstatus,") for instruction in instructions))

    def test_vsetvl_search_suite_final_elf_contains_vsetvl(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/vsetvl_interrupt_search_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)

        objdump = toolchain.resolve_objdump(toolchain.detect_toolchain())
        disasm_result = subprocess.run(
            [objdump, "-d", "--disassemble=vsetvl_interrupt_search_run", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, disasm_result.returncode, msg=disasm_result.stderr)
        self.assertIn("vsetvl\tzero,zero,zero", disasm_result.stdout)

    def test_split_store_search_suite_final_elf_contains_split_store_and_aligned_loads(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/misaligned_split_store_search_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)

        disasm_result = subprocess.run(
            [toolchain.resolve_objdump(toolchain.detect_toolchain()), "-d", "--disassemble=misaligned_split_store_search_run", str(artifact.elf_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, disasm_result.returncode, msg=disasm_result.stderr)
        instructions = []
        for line in disasm_result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) < 3:
                continue
            instructions.append("\t".join(field.strip() for field in fields[2:] if field.strip()))

        target_store_count = sum(
            1 for instruction in instructions
            if instruction.startswith("sd\t") and ",0(" in instruction
        )
        detector_load_count = sum(1 for instruction in instructions if instruction.startswith("lwu\t"))
        self.assertGreaterEqual(target_store_count, 17, msg=disasm_result.stdout)
        self.assertGreaterEqual(detector_load_count, 2, msg=disasm_result.stdout)
        self.assertTrue(any(instruction.startswith("lhu\t") for instruction in instructions), msg=disasm_result.stdout)
        self.assertTrue(any(instruction.startswith("lbu\t") for instruction in instructions), msg=disasm_result.stdout)

    def test_build_manifest_uses_xiangshan_linker_script(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/vsetvl_interrupt_path_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        manifest = json.loads((self.vsetvl_build_dir / "build_manifest.json").read_text())
        link_cmd = manifest["commands"]["link"]

        linker_arg = next(
            arg for arg in link_cmd
            if arg.startswith("-Wl,-T")
        )
        self.assertEqual(
            f'-Wl,-T{(ROOT / "runtime" / "platform" / "xiangshan" / "section.ld").resolve()}',
            linker_arg,
        )

    def test_prefetchw_tl_denied_fault_suite_build_generates_artifacts_and_manifest(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build", "suites/prefetchw_tl_denied_fault_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)

        generated_suite = self.prefetchw_build_dir / "generated_suite.c"
        test_elf = self.prefetchw_build_dir / "test.elf"
        test_bin = self.prefetchw_build_dir / "test.bin"
        disasm = self.prefetchw_build_dir / "disasm"
        build_manifest = self.prefetchw_build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
        self.assertTrue(disasm.is_file())
        self.assertTrue(build_manifest.is_file())

        manifest = json.loads(build_manifest.read_text())
        self.assertEqual("prefetchw_tl_denied_fault_poc", manifest["suite"])
        self.assertEqual(
            ["init_basic_env", "prefetchw_tl_denied_fault", "check_prefetchw_tl_denied_fault", "finish_check"],
            manifest["snippet_ids"],
        )
        self.assertEqual(str(generated_suite), manifest["artifacts"]["generated_suite"])
        self.assertEqual(str(test_elf), manifest["artifacts"]["elf"])
        self.assertEqual(str(test_bin), manifest["artifacts"]["bin"])
        self.assertEqual(str(disasm), manifest["artifacts"]["disasm"])
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])
        self.assertTrue(manifest["commands"]["compile"])
        self.assertTrue(manifest["commands"]["link"])
        self.assertTrue(manifest["commands"]["objcopy"])
        self.assertTrue(any("-march=rv64gcv_zicbop" in command for command in manifest["commands"]["compile"]))

    def test_prefetchw_tl_denied_fault_suite_final_elf_contains_load_then_prefetch_pair(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/prefetchw_tl_denied_fault_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)

        disasm_result = subprocess.run(
            [
                toolchain.resolve_objdump(toolchain.detect_toolchain()),
                "-d",
                "--disassemble=prefetchw_tl_denied_fault_run",
                str(artifact.elf_path),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, disasm_result.returncode, msg=disasm_result.stderr)
        self.assertRegex(
            disasm_result.stdout,
            r"(?s)\bld\s+\w+,0\((\w+)\).*?\bprefetch\.w\s+0\(\1\)",
        )
        self.assertIn(".word\t0x0005006b", disasm_result.stdout)
        self.assertEqual(1, disasm_result.stdout.count("prefetch.w"))
        self.assertIn("prefetch.w", disasm_result.stdout)
        self.assertNotIn("bnez", disasm_result.stdout)

    def test_cli_build_defaults_to_poc_suite(self) -> None:
        result = subprocess.run(
            ["python3", "generator/cli.py", "build"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertTrue((ROOT / "build" / "scalar_load_legality_poc" / "build_manifest.json").is_file())

    def test_build_artifact_paths_are_stable(self) -> None:
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        first = toolchain.artifact_paths_for_suite(ROOT, "scalar_load_legality_poc")
        second = toolchain.artifact_paths_for_suite(ROOT, "scalar_load_legality_poc")

        self.assertEqual(first.build_dir, second.build_dir)
        self.assertEqual(first.generated_suite_path, second.generated_suite_path)
        self.assertEqual(first.elf_path, second.elf_path)
        self.assertEqual(first.bin_path, second.bin_path)
        self.assertEqual(first.build_manifest_path, second.build_manifest_path)

    def test_objdump_resolves_from_detected_toolchain_directory(self) -> None:
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            tool_dir = Path(tmpdir)
            gcc_path = tool_dir / "riscv64-custom-gcc"
            objcopy_path = tool_dir / "riscv64-custom-objcopy"
            objdump_path = tool_dir / "riscv64-custom-objdump"

            for path in (gcc_path, objcopy_path, objdump_path):
                path.write_text("#!/bin/sh\nexit 0\n")
                path.chmod(0o755)

            resolved = toolchain.resolve_objdump(
                {
                    "prefix": "riscv64-custom",
                    "gcc": str(gcc_path),
                    "objcopy": str(objcopy_path),
                }
            )

            self.assertEqual(str(objdump_path), resolved)

    def test_missing_descriptor_causes_build_failure(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        model = importlib.import_module("generator.xsgen.model")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_descriptor_source = Path(tmpdir) / "broken_snippet.c"
            missing_descriptor_source.write_text("int broken_snippet_helper(void) { return 0; }\n")

            snippet = model.SnippetSpec(
                id="broken_snippet",
                kind="proc",
                lang="c",
                sources=(missing_descriptor_source.resolve(),),
            )
            plan = model.ComposePlan(
                suite_name="missing_descriptor_case",
                target="xiangshan-verilator",
                seed=1,
                snippet_ids=("broken_snippet",),
                snippets=(snippet,),
            )
            artifact = toolchain.artifact_paths_for_suite(ROOT, plan.suite_name)
            emitter.emit_harness(plan, artifact.generated_suite_path)

            with self.assertRaisesRegex(RuntimeError, "undefined reference|unresolved"):
                toolchain.build_artifacts(ROOT, plan, artifact)

    def test_duplicate_snippet_reference_builds_once_per_source(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            suite_path = Path(tmpdir) / "duplicate.yaml"
            suite_path.write_text(
                textwrap.dedent(
                    """
                    suite: duplicate_snippet_suite
                    target: xiangshan-verilator
                    seed: 5
                    compose:
                      mode: sequence
                      snippets:
                        - arm_timer
                        - arm_timer
                        - finish_check
                    """
                ).strip()
            )
            suite = suite_loader.load_suite(suite_path)
            plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
            artifact = toolchain.artifact_paths_for_suite(ROOT, plan.suite_name)
            emitter.emit_harness(plan, artifact.generated_suite_path)
            toolchain.build_artifacts(ROOT, plan, artifact)

            harness = artifact.generated_suite_path.read_text()
            self.assertEqual(2, harness.count("xsrt_run_snippet(&env, &snippet_arm_timer);"))
            manifest = json.loads(artifact.build_manifest_path.read_text())
            compile_sources = [
                cmd[cmd.index("-c") + 1]
                for cmd in manifest["commands"]["compile"]
            ]
            self.assertEqual(1, compile_sources.count(str((ROOT / "snippets" / "scalar_load_legality" / "arm_timer.c").resolve())))

    def test_missing_compile_input_causes_build_failure(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        model = importlib.import_module("generator.xsgen.model")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        missing_source = ROOT / "snippets" / "scalar_load_legality" / "does_not_exist.c"
        snippet = model.SnippetSpec(
            id="missing_source_snippet",
            kind="proc",
            lang="c",
            sources=(missing_source,),
        )
        plan = model.ComposePlan(
            suite_name="missing_source_case",
            target="xiangshan-verilator",
            seed=2,
            snippet_ids=("missing_source_snippet",),
            snippets=(snippet,),
        )
        artifact = toolchain.artifact_paths_for_suite(ROOT, plan.suite_name)
        emitter.emit_harness(plan, artifact.generated_suite_path)

        with self.assertRaisesRegex(RuntimeError, "No such file or directory|cannot find"):
            toolchain.build_artifacts(ROOT, plan, artifact)

    def test_objcopy_failure_is_reported(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/scalar_load_legality_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, "objcopy_failure_case")
        emitter.emit_harness(plan, artifact.generated_suite_path)

        broken_toolchain = dict(toolchain.detect_toolchain())
        broken_toolchain["objcopy"] = "/definitely/not/a/real/objcopy"

        with mock.patch.object(toolchain, "detect_toolchain", return_value=broken_toolchain):
            with self.assertRaisesRegex(RuntimeError, "objcopy"):
                toolchain.build_artifacts(ROOT, plan, artifact)

    def test_failed_rebuild_cleans_stale_outputs(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")
        emitter = importlib.import_module("generator.xsgen.emitter")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        suite = suite_loader.load_suite(ROOT / "suites/scalar_load_legality_poc.yaml")
        plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
        artifact = toolchain.artifact_paths_for_suite(ROOT, "stale_cleanup_case")

        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)
        self.assertTrue(artifact.elf_path.is_file())
        self.assertTrue(artifact.bin_path.is_file())
        self.assertTrue(artifact.build_manifest_path.is_file())

        artifact.generated_suite_path.write_text("broken harness\n")
        with self.assertRaises(RuntimeError):
            toolchain.build_artifacts(ROOT, plan, artifact)
        self.assertFalse(artifact.elf_path.exists())
        self.assertFalse(artifact.bin_path.exists())
        self.assertFalse(artifact.build_manifest_path.exists())

        emitter.emit_harness(plan, artifact.generated_suite_path)
        toolchain.build_artifacts(ROOT, plan, artifact)
        broken_toolchain = dict(toolchain.detect_toolchain())
        broken_toolchain["objcopy"] = "/definitely/not/a/real/objcopy"

        with mock.patch.object(toolchain, "detect_toolchain", return_value=broken_toolchain):
            with self.assertRaises(RuntimeError):
                toolchain.build_artifacts(ROOT, plan, artifact)
        self.assertFalse(artifact.elf_path.exists())
        self.assertFalse(artifact.bin_path.exists())
        self.assertFalse(artifact.build_manifest_path.exists())


if __name__ == "__main__":
    unittest.main()
