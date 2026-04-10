from pathlib import Path
import importlib
import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class RunPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_root = ROOT / "build" / "vsetvl_interrupt_path_poc" / "runs"
        if self.run_root.exists():
            shutil.rmtree(self.run_root)

    def test_normalize_seeds_accepts_single_list_and_range(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")

        self.assertEqual((1234,), run_batch.normalize_seeds(seed=1234, seeds=None, seed_range=None))
        self.assertEqual((1, 2, 3), run_batch.normalize_seeds(seed=None, seeds="1,2,3", seed_range=None))
        self.assertEqual((0, 1, 2, 3), run_batch.normalize_seeds(seed=None, seeds=None, seed_range="0:3"))

    def test_normalize_seeds_rejects_missing_selector_and_invalid_inputs(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")

        with self.assertRaisesRegex(ValueError, "one seed selector"):
            run_batch.normalize_seeds(seed=None, seeds=None, seed_range=None)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            run_batch.normalize_seeds(seed=-1, seeds=None, seed_range=None)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            run_batch.normalize_seeds(seed=None, seeds="1,2,2", seed_range=None)
        with self.assertRaisesRegex(ValueError, "invalid seed"):
            run_batch.normalize_seeds(seed=None, seeds="1,,3", seed_range=None)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            run_batch.normalize_seeds(seed=None, seeds="-1,2", seed_range=None)
        with self.assertRaisesRegex(ValueError, "invalid seed range"):
            run_batch.normalize_seeds(seed=None, seeds=None, seed_range="3:0")
        with self.assertRaisesRegex(ValueError, "non-negative"):
            run_batch.normalize_seeds(seed=None, seeds=None, seed_range="-1:1")

    def test_default_run_batch_ids_are_unique(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")

        first = run_batch._default_run_batch_id()
        second = run_batch._default_run_batch_id()

        self.assertNotEqual(first, second)

    def test_cli_run_invokes_batch_with_normalized_seeds(self) -> None:
        cli = importlib.import_module("generator.cli")

        with mock.patch.object(cli, "run_suite_batch", return_value=Path("/tmp/run-ledger.json")) as run_mock:
            rc = cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seeds", "4,5,6"])

        self.assertEqual(0, rc)
        run_mock.assert_called_once()
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(ROOT / "suites" / "vsetvl_interrupt_path_poc.yaml", kwargs["suite_path"])
        self.assertEqual((4, 5, 6), kwargs["seed_values"])

    def test_cli_run_invokes_batch_with_single_seed_and_range(self) -> None:
        cli = importlib.import_module("generator.cli")

        with mock.patch.object(cli, "run_suite_batch", return_value=Path("/tmp/run-ledger.json")) as run_mock:
            rc = cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seed", "7"])
        self.assertEqual(0, rc)
        self.assertEqual((7,), run_mock.call_args.kwargs["seed_values"])

        with mock.patch.object(cli, "run_suite_batch", return_value=Path("/tmp/run-ledger.json")) as run_mock:
            rc = cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seed-range", "8:10"])
        self.assertEqual(0, rc)
        self.assertEqual((8, 9, 10), run_mock.call_args.kwargs["seed_values"])

    def test_cli_run_reports_clean_seed_validation_error(self) -> None:
        cli = importlib.import_module("generator.cli")

        with self.assertRaises(SystemExit) as ctx:
            cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seeds", "1,,3"])
        self.assertEqual("invalid seed list contains an empty seed", str(ctx.exception))

    def test_cli_run_rejects_negative_seed_without_emitting_ledger(self) -> None:
        cli = importlib.import_module("generator.cli")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "run_ledger.json"
            with mock.patch.object(cli, "run_suite_batch", return_value=ledger_path) as run_mock:
                with self.assertRaises(SystemExit) as ctx:
                    cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seed", "-1"])

        self.assertIn("non-negative", str(ctx.exception))
        run_mock.assert_not_called()

    def test_run_batch_writes_seed_isolated_artifacts_and_ledger(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")
        model = importlib.import_module("generator.xsgen.model")

        def fake_target_loader(repo_root: Path, target: str):
            self.assertEqual(ROOT, repo_root)
            self.assertEqual("xiangshan-verilator", target)

            def run_target(*, artifacts, timeout_s):
                artifacts.stdout_log_path.write_text("fake stdout\n")
                artifacts.stderr_log_path.write_text("")
                return model.TargetRunResult(
                    status="ran",
                    labels=("built", "ran"),
                    notes="",
                    returncode=0,
                )

            return run_target

        ledger_path = run_batch.run_suite_batch(
            repo_root=ROOT,
            suite_path=ROOT / "suites" / "vsetvl_interrupt_path_poc.yaml",
            seed_values=(11, 12),
            target_loader=fake_target_loader,
            run_batch_id="test-batch",
        )

        self.assertTrue(ledger_path.is_file())
        ledger = json.loads(ledger_path.read_text())
        self.assertEqual("vsetvl_interrupt_path_poc", ledger["suite"])
        self.assertEqual("xiangshan-verilator", ledger["target"])
        self.assertEqual("test-batch", ledger["run_batch"])
        self.assertEqual([11, 12], [entry["seed"] for entry in ledger["entries"]])

        for seed in (11, 12):
            seed_dir = self.run_root / "test-batch" / f"seed_{seed}"
            with self.subTest(seed=seed):
                self.assertTrue((seed_dir / "generated_suite.c").is_file())
                self.assertTrue((seed_dir / "test.elf").is_file())
                self.assertTrue((seed_dir / "test.bin").is_file())
                self.assertTrue((seed_dir / "stdout.log").is_file())
                self.assertTrue((seed_dir / "stderr.log").is_file())
                self.assertTrue((seed_dir / "run_meta.json").is_file())

    def test_failed_run_still_writes_meta_and_logs(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")
        model = importlib.import_module("generator.xsgen.model")

        def fake_target_loader(repo_root: Path, target: str):
            def run_target(*, artifacts, timeout_s):
                artifacts.stdout_log_path.write_text("")
                artifacts.stderr_log_path.write_text("simulated failure\n")
                raise RuntimeError("simulated target adapter failure")

            return run_target

        ledger_path = run_batch.run_suite_batch(
            repo_root=ROOT,
            suite_path=ROOT / "suites" / "vsetvl_interrupt_path_poc.yaml",
            seed_values=(21,),
            target_loader=fake_target_loader,
            run_batch_id="failing-batch",
        )

        ledger = json.loads(ledger_path.read_text())
        self.assertEqual("error", ledger["entries"][0]["status"])
        self.assertIn("error", ledger["entries"][0]["labels"])

        seed_dir = self.run_root / "failing-batch" / "seed_21"
        self.assertTrue((seed_dir / "stdout.log").is_file())
        self.assertTrue((seed_dir / "stderr.log").is_file())
        self.assertTrue((seed_dir / "run_meta.json").is_file())


if __name__ == "__main__":
    unittest.main()
