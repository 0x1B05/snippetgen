from pathlib import Path
import importlib
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROUND2_FILES = [
    "generator/cli.py",
    "generator/xsgen/model.py",
    "generator/xsgen/snippet_db.py",
    "generator/xsgen/suite_loader.py",
    "snippets/core/init_basic_env.c",
    "snippets/core/finish_check.c",
    "snippets/scalar_load_legality/arm_timer.c",
    "snippets/scalar_load_legality/unaligned_load.c",
    "snippets/scalar_load_legality/check_scalar_load_legality.c",
    "snippets/manifests/init_basic_env.yaml",
    "snippets/manifests/finish_check.yaml",
    "snippets/manifests/arm_timer.yaml",
    "snippets/manifests/unaligned_load.yaml",
    "snippets/manifests/check_scalar_load_legality.yaml",
    "suites/scalar_load_legality_poc.yaml",
]


class SnippetLoadingTest(unittest.TestCase):
    def test_round2_files_exist(self) -> None:
        for relative_path in ROUND2_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_snippet_sources_compile(self) -> None:
        snippet_sources = [
            "snippets/core/init_basic_env.c",
            "snippets/core/finish_check.c",
            "snippets/scalar_load_legality/arm_timer.c",
            "snippets/scalar_load_legality/unaligned_load.c",
            "snippets/scalar_load_legality/check_scalar_load_legality.c",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            for relative_path in snippet_sources:
                src_path = ROOT / relative_path
                out_path = Path(tmpdir) / (src_path.stem + ".o")
                result = subprocess.run(
                    [
                        "cc",
                        "-std=c11",
                        "-Wall",
                        "-Wextra",
                        "-Werror",
                        "-I",
                        str(ROOT / "runtime/include"),
                        "-I",
                        str(ROOT / "snippets/include"),
                        "-c",
                        str(src_path),
                        "-o",
                        str(out_path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, msg=result.stderr)

    def test_real_manifest_db_and_suite_produce_deterministic_plan(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")

        db_first = snippet_db.load_snippet_db(ROOT)
        db_second = snippet_db.load_snippet_db(ROOT)
        self.assertEqual(sorted(db_first.keys()), sorted(db_second.keys()))

        suite = suite_loader.load_suite(ROOT / "suites/scalar_load_legality_poc.yaml")
        plan_first = suite_loader.build_compose_plan(suite, db_first)
        plan_second = suite_loader.build_compose_plan(suite, db_second)

        self.assertEqual(
            ("init_basic_env", "arm_timer", "unaligned_load", "check_scalar_load_legality", "finish_check"),
            plan_first.snippet_ids,
        )
        self.assertEqual(plan_first.snippet_ids, plan_second.snippet_ids)

    def test_manifest_loader_rejects_missing_fields_and_stream_kind(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_path = tmp_root / "demo.c"
            source_path.write_text("int demo(void) { return 0; }\n")

            missing_fields_manifest = tmp_root / "missing.yaml"
            missing_fields_manifest.write_text(
                textwrap.dedent(
                    """
                    id: demo
                    kind: proc
                    """
                ).strip()
            )

            stream_manifest = tmp_root / "stream.yaml"
            stream_manifest.write_text(
                textwrap.dedent(
                    """
                    id: demo
                    kind: stream
                    lang: c
                    sources:
                      - demo.c
                    """
                ).strip()
            )

            with self.assertRaises(ValueError):
                snippet_db.load_manifest(missing_fields_manifest, tmp_root)

            with self.assertRaises(ValueError):
                snippet_db.load_manifest(stream_manifest, tmp_root)

    def test_suite_loader_rejects_future_only_modes_and_unknown_snippets(self) -> None:
        snippet_db = importlib.import_module("generator.xsgen.snippet_db")
        suite_loader = importlib.import_module("generator.xsgen.suite_loader")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            future_mode_suite = tmp_root / "future.yaml"
            future_mode_suite.write_text(
                textwrap.dedent(
                    """
                    suite: bad_future
                    target: xiangshan-verilator
                    seed: 1
                    compose:
                      mode: weighted-mix
                      snippets:
                        - init_basic_env
                    """
                ).strip()
            )
            with self.assertRaises(ValueError):
                suite_loader.load_suite(future_mode_suite)

            real_db = snippet_db.load_snippet_db(ROOT)
            unknown_snippet_suite = tmp_root / "unknown.yaml"
            unknown_snippet_suite.write_text(
                textwrap.dedent(
                    """
                    suite: unknown_snippet
                    target: xiangshan-verilator
                    seed: 2
                    compose:
                      mode: sequence
                      snippets:
                        - does_not_exist
                    """
                ).strip()
            )
            suite = suite_loader.load_suite(unknown_snippet_suite)
            with self.assertRaises(ValueError):
                suite_loader.build_compose_plan(suite, real_db)

    def test_cli_dump_plan_and_list_snippets(self) -> None:
        list_result = subprocess.run(
            ["python3", "generator/cli.py", "list-snippets"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, list_result.returncode, msg=list_result.stderr)
        self.assertIn("init_basic_env", list_result.stdout)
        self.assertIn("finish_check", list_result.stdout)

        dump_result = subprocess.run(
            ["python3", "generator/cli.py", "dump-plan", "suites/scalar_load_legality_poc.yaml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, dump_result.returncode, msg=dump_result.stderr)
        plan = json.loads(dump_result.stdout)
        self.assertEqual("scalar_load_legality_poc", plan["suite"])
        self.assertEqual(
            ["init_basic_env", "arm_timer", "unaligned_load", "check_scalar_load_legality", "finish_check"],
            plan["snippet_ids"],
        )

    def test_cli_build_is_explicit_and_not_a_false_positive(self) -> None:
        result = subprocess.run(
            ["make", "build"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("not implemented", result.stderr.lower() + result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
