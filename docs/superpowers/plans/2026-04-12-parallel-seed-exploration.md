# Parallel Seed Exploration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-pass `--jobs` option that parallelizes only the `run` phase of multi-seed execution while preserving per-seed isolation and stable batch ledger ordering.

**Architecture:** Keep `emit/build` serial in `run_suite_batch()`, then submit prepared per-seed run tasks into a fixed-size `ThreadPoolExecutor`. Workers return completed seed results; the main thread writes `run_meta.json` and the final batch ledger in input order.

**Tech Stack:** Python 3, `argparse`, `concurrent.futures.ThreadPoolExecutor`, existing unittest suite

---

### Task 1: Add CLI Coverage For `--jobs`

**Files:**
- Modify: `tests/test_run_pipeline.py`
- Modify: `generator/cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Add tests to [`tests/test_run_pipeline.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/tests/test_run_pipeline.py) covering:

```python
    def test_cli_run_passes_jobs_to_batch_runner(self) -> None:
        cli = importlib.import_module("generator.cli")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "run_ledger.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "suite": "demo",
                        "target": "xiangshan-verilator",
                        "run_batch": "batch",
                        "entries": [{"seed": 4, "status": "ran", "labels": ["built", "ran"]}],
                    }
                )
            )
            with mock.patch.object(cli, "run_suite_batch", return_value=ledger_path) as run_mock:
                rc = cli.main(
                    [
                        "run",
                        "suites/vsetvl_interrupt_path_poc.yaml",
                        "--seeds",
                        "4,5,6",
                        "--jobs",
                        "3",
                    ]
                )

        self.assertEqual(0, rc)
        self.assertEqual(3, run_mock.call_args.kwargs["jobs"])

    def test_cli_run_defaults_jobs_to_one(self) -> None:
        cli = importlib.import_module("generator.cli")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "run_ledger.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "suite": "demo",
                        "target": "xiangshan-verilator",
                        "run_batch": "batch",
                        "entries": [{"seed": 7, "status": "ran", "labels": ["built", "ran"]}],
                    }
                )
            )
            with mock.patch.object(cli, "run_suite_batch", return_value=ledger_path) as run_mock:
                rc = cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seed", "7"])

        self.assertEqual(0, rc)
        self.assertEqual(1, run_mock.call_args.kwargs["jobs"])

    def test_cli_run_rejects_non_positive_jobs(self) -> None:
        cli = importlib.import_module("generator.cli")

        with self.assertRaises(SystemExit) as ctx:
            cli.main(["run", "suites/vsetvl_interrupt_path_poc.yaml", "--seed", "7", "--jobs", "0"])

        self.assertIn("jobs must be positive", str(ctx.exception))
```

- [ ] **Step 2: Run the targeted CLI tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_cli_run_passes_jobs_to_batch_runner tests.test_run_pipeline.RunPipelineTest.test_cli_run_defaults_jobs_to_one tests.test_run_pipeline.RunPipelineTest.test_cli_run_rejects_non_positive_jobs
```

Expected:

- at least the first two tests fail because `jobs` is not passed
- the validation test fails because `--jobs` is not implemented yet

- [ ] **Step 3: Implement minimal CLI support**

Update [`generator/cli.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/generator/cli.py):

```python
def cmd_run(args: argparse.Namespace) -> int:
    try:
        seed_values = normalize_seeds(seed=args.seed, seeds=args.seeds, seed_range=args.seed_range)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.jobs < 1:
        raise SystemExit("jobs must be positive")
    ledger_path = run_suite_batch(
        repo_root=REPO_ROOT,
        suite_path=REPO_ROOT / Path(args.suite),
        seed_values=seed_values,
        run_batch_id=args.batch_id,
        timeout_s=args.timeout_sec,
        jobs=args.jobs,
    )
    print(ledger_path)
    return _run_exit_code(ledger_path)
```

And extend the parser:

```python
    run_parser.add_argument("--jobs", type=int, default=1)
```

- [ ] **Step 4: Re-run the targeted CLI tests and verify they pass**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_cli_run_passes_jobs_to_batch_runner tests.test_run_pipeline.RunPipelineTest.test_cli_run_defaults_jobs_to_one tests.test_run_pipeline.RunPipelineTest.test_cli_run_rejects_non_positive_jobs
```

Expected:

- all three tests pass

- [ ] **Step 5: Commit the CLI slice**

```bash
git add tests/test_run_pipeline.py generator/cli.py
git commit -m "feat: add jobs option to run cli"
```

### Task 2: Add Batch-Level Concurrency Tests

**Files:**
- Modify: `tests/test_run_pipeline.py`
- Modify: `generator/xsgen/run_batch.py`

- [ ] **Step 1: Write the failing batch concurrency tests**

Add tests to [`tests/test_run_pipeline.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/tests/test_run_pipeline.py) for:

```python
    def test_run_batch_preserves_input_seed_order_under_parallel_completion(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")
        completion_order: list[int] = []

        def fake_target_loader(repo_root: Path, target: str):
            def run_target(*, artifacts, timeout_s):
                if artifacts.seed == 11:
                    time.sleep(0.05)
                else:
                    time.sleep(0.01)
                completion_order.append(artifacts.seed)
                return run_batch.TargetRunResult(
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
            run_batch_id="parallel-order",
            timeout_s=5,
            jobs=2,
        )

        payload = json.loads(ledger_path.read_text())
        self.assertEqual([12, 11], completion_order)
        self.assertEqual([11, 12], [entry["seed"] for entry in payload["entries"]])

    def test_run_batch_continues_other_runs_when_one_seed_errors(self) -> None:
        run_batch = importlib.import_module("generator.xsgen.run_batch")
        seen: list[int] = []

        def fake_target_loader(repo_root: Path, target: str):
            def run_target(*, artifacts, timeout_s):
                seen.append(artifacts.seed)
                if artifacts.seed == 21:
                    raise RuntimeError("simulated run failure")
                return run_batch.TargetRunResult(
                    status="ran",
                    labels=("built", "ran"),
                    notes="",
                    returncode=0,
                )

            return run_target

        ledger_path = run_batch.run_suite_batch(
            repo_root=ROOT,
            suite_path=ROOT / "suites" / "vsetvl_interrupt_path_poc.yaml",
            seed_values=(21, 22),
            target_loader=fake_target_loader,
            run_batch_id="parallel-failure",
            timeout_s=5,
            jobs=2,
        )

        payload = json.loads(ledger_path.read_text())
        self.assertEqual([21, 22], sorted(seen))
        self.assertEqual(["error", "ran"], [entry["status"] for entry in payload["entries"]])
```

- [ ] **Step 2: Run the targeted batch tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_preserves_input_seed_order_under_parallel_completion tests.test_run_pipeline.RunPipelineTest.test_run_batch_continues_other_runs_when_one_seed_errors
```

Expected:

- tests fail because `run_suite_batch()` has no `jobs` parameter and no parallel scheduling yet

- [ ] **Step 3: Add a minimal `jobs` parameter to the batch API**

Change the signature in [`generator/xsgen/run_batch.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/generator/xsgen/run_batch.py):

```python
def run_suite_batch(
    *,
    repo_root: Path,
    suite_path: Path,
    seed_values: tuple[int, ...],
    target_loader=load_run_target,
    run_batch_id: str | None = None,
    timeout_s: int | None = None,
    jobs: int = 1,
) -> Path:
```

Add an early guard:

```python
    if jobs < 1:
        raise ValueError(f"jobs must be positive: {jobs}")
```

- [ ] **Step 4: Re-run the targeted batch tests and confirm they still fail for the right reason**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_preserves_input_seed_order_under_parallel_completion tests.test_run_pipeline.RunPipelineTest.test_run_batch_continues_other_runs_when_one_seed_errors
```

Expected:

- failures now point at missing parallel scheduling behavior rather than missing function arguments

- [ ] **Step 5: Commit the test scaffold slice**

```bash
git add tests/test_run_pipeline.py generator/xsgen/run_batch.py
git commit -m "test: add parallel run batch expectations"
```

### Task 3: Separate Seed Preparation From Seed Run

**Files:**
- Modify: `generator/xsgen/run_batch.py`
- Test: `tests/test_run_pipeline.py`

- [ ] **Step 1: Introduce preparation helpers with no concurrency yet**

Refactor [`generator/xsgen/run_batch.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/generator/xsgen/run_batch.py) so the current body is split into helpers similar to:

```python
def _prepare_seed_run(...):
    suite = replace(base_suite, seed=seed)
    plan = build_compose_plan(suite, snippet_db)
    artifact = artifact_paths_for_run_seed(repo_root, plan.suite_name, run_batch, seed)
    stdout_log_path = artifact.build_dir / "stdout.log"
    stderr_log_path = artifact.build_dir / "stderr.log"
    run_meta_path = artifact.build_dir / "run_meta.json"
    wave_path = artifact.build_dir / "lightsss-wave"
    _ensure_log_files(stdout_log_path, stderr_log_path)
    emit_harness(plan, artifact.generated_suite_path)
    build_artifacts(repo_root, plan, artifact)
    return RunSeedArtifacts(...), artifact, stdout_log_path, stderr_log_path, run_meta_path, wave_path, plan

def _error_entry(...):
    return RunEntry(...)
```

Do not parallelize yet in this step; only make the boundaries explicit.

- [ ] **Step 2: Run the existing serial batch tests**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_seed_isolated_artifacts_and_batch_meta tests.test_run_pipeline.RunPipelineTest.test_run_batch_records_build_or_adapter_failures_per_seed tests.test_run_pipeline.RunPipelineTest.test_run_batch_generates_unique_default_batch_ids
```

Expected:

- all tests stay green

- [ ] **Step 3: Add a helper for turning a run result into a final entry**

Add a focused helper in [`generator/xsgen/run_batch.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/generator/xsgen/run_batch.py):

```python
def _completed_entry(*, plan, artifact, stdout_log_path, stderr_log_path, run_meta_path, wave_path, run_batch, seed, target_result):
    return RunEntry(
        suite_name=plan.suite_name,
        target=plan.target,
        run_batch=run_batch,
        seed=seed,
        artifact_dir=artifact.build_dir,
        elf_path=artifact.elf_path,
        bin_path=artifact.bin_path,
        disasm_path=artifact.disasm_path,
        stdout_log_path=stdout_log_path,
        stderr_log_path=stderr_log_path,
        run_meta_path=run_meta_path,
        wave_path=wave_path,
        status=target_result.status,
        labels=target_result.labels,
        notes=target_result.notes,
        returncode=target_result.returncode,
    )
```

- [ ] **Step 4: Re-run the same serial tests**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_seed_isolated_artifacts_and_batch_meta tests.test_run_pipeline.RunPipelineTest.test_run_batch_records_build_or_adapter_failures_per_seed tests.test_run_pipeline.RunPipelineTest.test_run_batch_generates_unique_default_batch_ids
```

Expected:

- all tests pass

- [ ] **Step 5: Commit the preparation refactor**

```bash
git add generator/xsgen/run_batch.py
git commit -m "refactor: split seed preparation from run execution"
```

### Task 4: Implement Parallel Run Scheduling

**Files:**
- Modify: `generator/xsgen/run_batch.py`
- Test: `tests/test_run_pipeline.py`

- [ ] **Step 1: Implement the worker pool**

Update [`generator/xsgen/run_batch.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/generator/xsgen/run_batch.py) to:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

And implement run scheduling roughly as:

```python
    prepared = []
    entries_by_seed: dict[int, RunEntry] = {}

    for seed in seed_values:
        try:
            prepared_item = _prepare_seed_run(...)
            prepared.append(prepared_item)
        except Exception as exc:
            stderr_log_path.write_text(f"{exc}\n")
            entry = _error_entry(...)
            _write_run_meta(entry)
            entries_by_seed[seed] = entry

    max_workers = min(jobs, len(prepared)) if prepared else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(target_runner, artifacts=item.run_artifacts, timeout_s=timeout_s): item
            for item in prepared
        }
        for future in as_completed(future_map):
            item = future_map[future]
            try:
                target_result = future.result()
            except Exception as exc:
                item.stderr_log_path.write_text(f"{exc}\n")
                target_result = TargetRunResult(status="error", labels=("error",), notes=str(exc), returncode=None)
            entry = _completed_entry(..., target_result=target_result)
            _write_run_meta(entry)
            entries_by_seed[item.seed] = entry

    ordered_entries = [entries_by_seed[seed] for seed in seed_values]
```

- [ ] **Step 2: Run the new concurrency tests**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_preserves_input_seed_order_under_parallel_completion tests.test_run_pipeline.RunPipelineTest.test_run_batch_continues_other_runs_when_one_seed_errors
```

Expected:

- both tests pass

- [ ] **Step 3: Run the existing batch behavior tests**

Run:

```bash
python3 -m unittest tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_seed_isolated_artifacts_and_batch_meta tests.test_run_pipeline.RunPipelineTest.test_run_batch_records_build_or_adapter_failures_per_seed tests.test_run_pipeline.RunPipelineTest.test_run_batch_generates_unique_default_batch_ids
```

Expected:

- all tests pass

- [ ] **Step 4: Commit the scheduler implementation**

```bash
git add generator/xsgen/run_batch.py tests/test_run_pipeline.py
git commit -m "feat: parallelize run stage with worker pool"
```

### Task 5: Verify Full Run Surface

**Files:**
- Modify: `tests/test_run_pipeline.py`
- Modify: `docs/release-notes-2026-04-11.md`

- [ ] **Step 1: Add an integration-level CLI test for `--jobs`**

Add one more test in [`tests/test_run_pipeline.py`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/tests/test_run_pipeline.py) that asserts the CLI passes both seeds and jobs together:

```python
    def test_cli_run_passes_jobs_and_batch_id_together(self) -> None:
        cli = importlib.import_module("generator.cli")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "run_ledger.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "suite": "demo",
                        "target": "xiangshan-verilator",
                        "run_batch": "batch",
                        "entries": [{"seed": 1, "status": "ran", "labels": ["built", "ran"]}],
                    }
                )
            )
            with mock.patch.object(cli, "run_suite_batch", return_value=ledger_path) as run_mock:
                rc = cli.main(
                    [
                        "run",
                        "suites/vsetvl_interrupt_path_poc.yaml",
                        "--seeds",
                        "1,2",
                        "--jobs",
                        "2",
                        "--batch-id",
                        "parallel-demo",
                    ]
                )

        self.assertEqual(0, rc)
        self.assertEqual(2, run_mock.call_args.kwargs["jobs"])
        self.assertEqual("parallel-demo", run_mock.call_args.kwargs["run_batch_id"])
```

- [ ] **Step 2: Update release notes**

Append a short note to [`docs/release-notes-2026-04-11.md`](/home/dfpmts/.config/superpowers/worktrees/snippetgen-demo/parallel-seed-exploration/docs/release-notes-2026-04-11.md):

```md
### Parallel run execution

`snippetgen run` now accepts `--jobs <N>` to run multiple prepared seed workloads concurrently in the `emu` execution phase.

- default remains serial: `--jobs 1`
- build artifacts are still prepared serially
- per-seed outputs remain isolated
- final batch ledger remains ordered by input seed
```

- [ ] **Step 3: Run the focused full run test file**

Run:

```bash
python3 -m unittest tests.test_run_pipeline
```

Expected:

- all run pipeline tests pass

- [ ] **Step 4: Run the full project test suite**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected:

- all tests pass

- [ ] **Step 5: Commit the final verification slice**

```bash
git add tests/test_run_pipeline.py docs/release-notes-2026-04-11.md
git commit -m "docs: document parallel seed exploration"
```
