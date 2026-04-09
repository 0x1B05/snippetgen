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
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

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
        build_manifest = self.build_dir / "build_manifest.json"

        self.assertTrue(generated_suite.is_file())
        self.assertTrue(test_elf.is_file())
        self.assertTrue(test_bin.is_file())
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
        self.assertEqual(str(build_manifest), manifest["artifacts"]["build_manifest"])
        self.assertTrue(manifest["commands"]["compile"])
        self.assertTrue(manifest["commands"]["objcopy"])

    def test_build_artifact_paths_are_stable(self) -> None:
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        first = toolchain.artifact_paths_for_suite(ROOT, "scalar_load_legality_poc")
        second = toolchain.artifact_paths_for_suite(ROOT, "scalar_load_legality_poc")

        self.assertEqual(first.build_dir, second.build_dir)
        self.assertEqual(first.generated_suite_path, second.generated_suite_path)
        self.assertEqual(first.elf_path, second.elf_path)
        self.assertEqual(first.bin_path, second.bin_path)
        self.assertEqual(first.build_manifest_path, second.build_manifest_path)

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


if __name__ == "__main__":
    unittest.main()
