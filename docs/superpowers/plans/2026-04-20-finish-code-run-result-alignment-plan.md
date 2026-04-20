# Finish Code Run Result Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve and expose guest semantic finish codes from snippet and AM return paths through the XiangShan runner and into `run_meta.json` / `batch_meta.json`.

**Architecture:** Keep the guest-side contract unchanged. The generated harness already returns snippet failure codes from `main()`, and XiangShan already interprets trap codes as `0 => HIT GOOD TRAP`, `1 => HIT BAD TRAP`, `>1 => Unknown trap code: N`. The work is to decode that trap-code contract in `targets/xiangshan-verilator/run_target.py`, thread a new `finish_code` field through `TargetRunResult` and `RunEntry`, and serialize it into run metadata so downstream tooling can consume exact failure semantics instead of only `good_trap` / `bad_trap`.

**Tech Stack:** Python 3, `unittest`, existing `generator.xsgen` dataclasses, XiangShan `emu` log format, JSON run metadata.

---

## File Map

- Modify: `targets/xiangshan-verilator/run_target.py`
  Decode `HIT GOOD TRAP`, `HIT BAD TRAP`, and `Unknown trap code: N` into a structured `finish_code`.
- Modify: `generator/xsgen/model.py`
  Add `finish_code` to `TargetRunResult` and `RunEntry`.
- Modify: `generator/xsgen/run_batch.py`
  Persist `finish_code` into `run_meta.json` and `batch_meta.json`.
- Modify: `tests/test_run_pipeline.py`
  Lock the runner classification and metadata persistence contract before implementation.
- Modify: `README.md`
  Document the new metadata field and its meaning.

## Guardrails

- Do not change `generator/xsgen/emitter.py` in this pass. The current harness already preserves the snippet return value by returning `rc` from `main()`.
- Do not change `runtime/arch/riscv64/start.S` in this pass. `_start` already traps immediately after `main()` returns, leaving `a0` as the guest trap code.
- Keep CLI exit semantics unchanged in `generator/cli.py`. `snippetgen run` should still succeed only when every entry has `status == "ran"`.
- Treat `finish_code` as supplementary metadata. Existing `status`, `labels`, and `notes` remain the primary backwards-compatible classification surface.

### Task 1: Lock the Semantic Finish-Code Contract in Tests

**Files:**
- Modify: `tests/test_run_pipeline.py`
- Verify: `/home/dfpmts/XS/xs-env/XiangShan/difftest/src/test/csrc/common/common.h`
- Verify: `/home/dfpmts/XS/xs-env/XiangShan/difftest/src/test/csrc/emu/emu.cpp`

- [ ] **Step 1: Add a failing runner test for `Unknown trap code: N`**

```python
def test_xiangshan_runner_classifies_unknown_trap_code_from_logs(self) -> None:
    module_path = ROOT / "targets" / "xiangshan-verilator" / "run_target.py"
    spec = importlib.util.spec_from_file_location("xiangshan_run_target_unknown_trap_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    model = importlib.import_module("generator.xsgen.model")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        xs_env_root = root / "xs-env"
        env_sh = xs_env_root / "env.sh"
        emu_path = xs_env_root / "XiangShan" / "build" / "verilator-compile" / "emu"
        diff_path = xs_env_root / "NEMU" / "build" / "riscv64-nemu-interpreter-so"
        build_dir = root / "build"
        bin_path = build_dir / "test.bin"
        elf_path = build_dir / "test.elf"
        stdout_log_path = build_dir / "stdout.log"
        stderr_log_path = build_dir / "stderr.log"
        run_meta_path = build_dir / "run_meta.json"

        emu_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        build_dir.mkdir(parents=True, exist_ok=True)

        env_sh.write_text("#!/bin/sh\n")
        emu_path.write_text("#!/bin/sh\nexit 1\n")
        emu_path.chmod(0o755)
        diff_path.write_text("stub diff\n")
        bin_path.write_bytes(b"\x00")
        elf_path.write_bytes(b"\x00")
        stdout_log_path.write_text("")
        stderr_log_path.write_text("")

        artifacts = model.RunSeedArtifacts(
            suite_name="demo",
            target="xiangshan-verilator",
            seed=4660,
            run_batch="batch",
            build_artifact=model.BuildArtifact(
                suite_name="demo",
                build_dir=build_dir,
                generated_suite_path=build_dir / "generated_suite.c",
                elf_path=elf_path,
                bin_path=bin_path,
                build_manifest_path=build_dir / "build_manifest.json",
            ),
            stdout_log_path=stdout_log_path,
            stderr_log_path=stderr_log_path,
            run_meta_path=run_meta_path,
        )

        def fake_run(command, **kwargs):
            kwargs["stderr"].write("Core 0: Unknown trap code: 27\n")
            kwargs["stderr"].flush()
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.dict(module.os.environ, {"SNIPPETGEN_XS_ENV_SH": str(env_sh)}, clear=False):
            with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
                result = module.run_target(artifacts=artifacts, timeout_s=5)

    self.assertEqual("bad_trap", result.status)
    self.assertIn("bad_trap", result.labels)
    self.assertEqual("Unknown trap code: 27", result.notes)
    self.assertEqual(27, result.finish_code)
```

- [ ] **Step 2: Add a failing batch-metadata test for persisted `finish_code`**

```python
def test_run_batch_writes_finish_code_to_run_meta_and_batch_meta(self) -> None:
    run_batch = importlib.import_module("generator.xsgen.run_batch")
    model = importlib.import_module("generator.xsgen.model")

    def fake_target_loader(repo_root: Path, target: str):
        def run_target(*, artifacts, timeout_s):
            artifacts.stdout_log_path.write_text("")
            artifacts.stderr_log_path.write_text("Core 0: Unknown trap code: 27\n")
            return model.TargetRunResult(
                status="bad_trap",
                labels=("built", "ran", "bad_trap"),
                notes="Unknown trap code: 27",
                returncode=0,
                finish_code=27,
            )

        return run_target

    ledger_path = run_batch.run_suite_batch(
        repo_root=ROOT,
        suite_path=ROOT / "suites" / "vsetvl_interrupt_path_poc.yaml",
        seed_values=(11,),
        target_loader=fake_target_loader,
        run_batch_id="finish-code-batch",
    )

    ledger = json.loads(ledger_path.read_text())
    seed_dir = self.run_root / "finish-code-batch" / "seed_11"
    run_meta = json.loads((seed_dir / "run_meta.json").read_text())

    self.assertEqual(27, ledger["entries"][0]["finish_code"])
    self.assertEqual(27, run_meta["finish_code"])
```

- [ ] **Step 3: Confirm XiangShan trap-code semantics from upstream source**

Run:

```bash
sed -n '48,49p' /home/dfpmts/XS/xs-env/XiangShan/difftest/src/test/csrc/common/common.h
sed -n '638,650p' /home/dfpmts/XS/xs-env/XiangShan/difftest/src/test/csrc/emu/emu.cpp
```

Expected:

```text
STATE_GOODTRAP = 0,
STATE_BADTRAP = 1,
...
case STATE_GOODTRAP: ... HIT GOOD TRAP ...
case STATE_BADTRAP: ... HIT BAD TRAP ...
default: ... Unknown trap code: %d
```

- [ ] **Step 4: Run the new tests and verify they fail before implementation**

Run:

```bash
python3 -m unittest \
  tests.test_run_pipeline.RunPipelineTest.test_xiangshan_runner_classifies_unknown_trap_code_from_logs \
  tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_finish_code_to_run_meta_and_batch_meta -v
```

Expected: FAIL because `TargetRunResult` and the serialized run metadata do not expose `finish_code` yet.

- [ ] **Step 5: Commit the red tests**

```bash
git add tests/test_run_pipeline.py
git commit -m "test: lock finish code runner contract"
```

### Task 2: Thread `finish_code` Through the Result Model and Batch Metadata

**Files:**
- Modify: `generator/xsgen/model.py`
- Modify: `generator/xsgen/run_batch.py`
- Test: `tests/test_run_pipeline.py`

- [ ] **Step 1: Extend the dataclasses with a nullable `finish_code` field**

```python
@dataclass(frozen=True)
class TargetRunResult:
    status: str
    labels: tuple[str, ...]
    notes: str
    returncode: int | None = None
    finish_code: int | None = None


@dataclass(frozen=True)
class RunEntry:
    suite_name: str
    target: str
    run_batch: str
    seed: int
    artifact_dir: Path
    elf_path: Path
    bin_path: Path
    disasm_path: Path | None
    stdout_log_path: Path
    stderr_log_path: Path
    run_meta_path: Path
    wave_path: Path | None
    status: str
    labels: tuple[str, ...]
    notes: str
    returncode: int | None = None
    finish_code: int | None = None
```

- [ ] **Step 2: Persist the new field in `run_meta.json` and `batch_meta.json`**

```python
def _entry_payload(entry: RunEntry) -> dict:
    return {
        "suite": entry.suite_name,
        "target": entry.target,
        "run_batch": entry.run_batch,
        "seed": entry.seed,
        "artifact_dir": str(entry.artifact_dir),
        "elf": str(entry.elf_path),
        "bin": str(entry.bin_path),
        "disasm": str(entry.disasm_path) if entry.disasm_path is not None else None,
        "stdout_log": str(entry.stdout_log_path),
        "stderr_log": str(entry.stderr_log_path),
        "run_meta": str(entry.run_meta_path),
        "wave_path": str(entry.wave_path) if entry.wave_path is not None else None,
        "status": entry.status,
        "labels": list(entry.labels),
        "notes": entry.notes,
        "returncode": entry.returncode,
        "finish_code": entry.finish_code,
    }
```

- [ ] **Step 3: Carry `finish_code` through `_completed_entry()`**

```python
def _completed_entry(
    *,
    prepared: _PreparedSeedRun,
    target_result: TargetRunResult,
) -> RunEntry:
    return RunEntry(
        suite_name=prepared.plan.suite_name,
        target=prepared.plan.target,
        run_batch=prepared.run_artifacts.run_batch,
        seed=prepared.seed,
        artifact_dir=prepared.artifact.build_dir,
        elf_path=prepared.artifact.elf_path,
        bin_path=prepared.artifact.bin_path,
        disasm_path=prepared.artifact.disasm_path,
        stdout_log_path=prepared.stdout_log_path,
        stderr_log_path=prepared.stderr_log_path,
        run_meta_path=prepared.run_meta_path,
        wave_path=prepared.wave_path,
        status=target_result.status,
        labels=target_result.labels,
        notes=target_result.notes,
        returncode=target_result.returncode,
        finish_code=target_result.finish_code,
    )
```

- [ ] **Step 4: Re-run the metadata tests**

Run:

```bash
python3 -m unittest \
  tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_finish_code_to_run_meta_and_batch_meta \
  tests.test_run_pipeline.RunPipelineTest.test_run_batch_writes_seed_isolated_artifacts_and_batch_meta -v
```

Expected: PASS, with `finish_code` present in both the per-seed and batch JSON payloads.

- [ ] **Step 5: Commit the schema and metadata wiring**

```bash
git add generator/xsgen/model.py generator/xsgen/run_batch.py tests/test_run_pipeline.py
git commit -m "feat: persist semantic finish codes in run metadata"
```

### Task 3: Decode Trap-Code Semantics in the XiangShan Runner

**Files:**
- Modify: `targets/xiangshan-verilator/run_target.py`
- Test: `tests/test_run_pipeline.py`

- [ ] **Step 1: Add a dedicated trap-code extraction helper**

```python
import re

_UNKNOWN_TRAP_RE = re.compile(r"Unknown trap code:\\s*(\\d+)")


def _extract_finish_code(merged: str) -> int | None:
    if "HIT GOOD TRAP" in merged:
        return 0
    if "HIT BAD TRAP" in merged:
        return 1
    match = _UNKNOWN_TRAP_RE.search(merged)
    if match is not None:
        return int(match.group(1))
    return None
```

- [ ] **Step 2: Update `_classify_result()` to attach `finish_code` without changing status semantics**

```python
def _classify_result(*, stdout_text: str, stderr_text: str, returncode: int) -> TargetRunResult:
    merged = f"{stdout_text}\\n{stderr_text}"
    finish_code = _extract_finish_code(merged)
    unknown_match = _UNKNOWN_TRAP_RE.search(merged)

    if "HIT GOOD TRAP" in merged:
        return TargetRunResult(
            status="ran",
            labels=("built", "ran", "good_trap"),
            notes="HIT GOOD TRAP",
            returncode=returncode,
            finish_code=0,
        )

    if unknown_match is not None:
        code = int(unknown_match.group(1))
        return TargetRunResult(
            status="bad_trap",
            labels=("built", "ran", "bad_trap"),
            notes=f"Unknown trap code: {code}",
            returncode=returncode,
            finish_code=code,
        )

    if "HIT BAD TRAP" in merged:
        return TargetRunResult(
            status="bad_trap",
            labels=("built", "ran", "bad_trap"),
            notes="HIT BAD TRAP",
            returncode=returncode,
            finish_code=1,
        )

    ...
```

- [ ] **Step 3: Add a regression test that `HIT BAD TRAP` maps to `finish_code == 1`**

```python
def test_xiangshan_runner_sets_finish_code_one_for_bad_trap(self) -> None:
    ...

    def fake_run(command, **kwargs):
        kwargs["stdout"].write("Core 0: HIT BAD TRAP at pc = 0x8000002c\\n")
        kwargs["stdout"].flush()
        return subprocess.CompletedProcess(command, 1)

    ...

    self.assertEqual("bad_trap", result.status)
    self.assertEqual(1, result.finish_code)
```

- [ ] **Step 4: Run the runner-focused subset**

Run:

```bash
python3 -m unittest \
  tests.test_run_pipeline.RunPipelineTest.test_xiangshan_runner_classifies_bad_trap_from_logs \
  tests.test_run_pipeline.RunPipelineTest.test_xiangshan_runner_classifies_unknown_trap_code_from_logs \
  tests.test_run_pipeline.RunPipelineTest.test_xiangshan_runner_sets_finish_code_one_for_bad_trap -v
```

Expected: PASS, with `0 / 1 / N` finish codes attached to `good_trap`, `bad_trap`, and `Unknown trap code: N` results respectively.

- [ ] **Step 5: Commit the runner decoding**

```bash
git add targets/xiangshan-verilator/run_target.py tests/test_run_pipeline.py
git commit -m "feat: decode semantic finish codes from xiangshan trap logs"
```

### Task 4: Document the Contract and Run the Full Regression Slice

**Files:**
- Modify: `README.md`
- Verify: `tests/test_run_pipeline.py`
- Verify: `tests/test_build_pipeline.py`

- [ ] **Step 1: Document the new field in `README.md`**

```markdown
Each `run_meta.json` entry now includes `finish_code`:

- `0`: guest ended with `HIT GOOD TRAP`
- `1`: guest ended with `HIT BAD TRAP`
- `N > 1`: XiangShan printed `Unknown trap code: N`
- `null`: the run did not end through the guest trap path, or the runner could not recover a semantic trap code
```

- [ ] **Step 2: Re-run the focused regression bucket**

Run:

```bash
python3 -m unittest \
  tests.test_run_pipeline \
  tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_prefetchw_tl_denied_fault_suite_build_generates_artifacts_and_manifest -v
```

Expected: PASS.

- [ ] **Step 3: Re-run the current local regression slice used for AM baseline work**

Run:

```bash
python3 -m unittest \
  tests.test_runtime_surface \
  tests.test_xsam_cte_behavior \
  tests.test_platform_driver_layer \
  tests.test_xsam_vme_behavior \
  tests.test_am_program_snippet_runtime \
  tests.test_am_program_snippet_build \
  tests.test_am_program_snippet_run \
  tests.test_build_pipeline \
  tests.test_snippet_loading \
  tests.test_run_pipeline
```

Expected: PASS.

- [ ] **Step 4: Record the result in the working notes or checkpoint doc**

```markdown
- Added `finish_code` to `TargetRunResult`, `RunEntry`, `run_meta.json`, and `batch_meta.json`
- XiangShan runner now decodes `0`, `1`, and `Unknown trap code: N`
- Existing CLI success semantics remain unchanged
```

- [ ] **Step 5: Commit the docs and final verification**

```bash
git add README.md tests/test_run_pipeline.py
git commit -m "docs: describe finish code run metadata contract"
```

## Acceptance Criteria

- `TargetRunResult` and `RunEntry` expose `finish_code: int | None`.
- `run_meta.json` and `batch_meta.json` include a `finish_code` field for every entry.
- XiangShan runner classifies:
  - `HIT GOOD TRAP` as `status="ran"` and `finish_code=0`
  - `HIT BAD TRAP` as `status="bad_trap"` and `finish_code=1`
  - `Unknown trap code: N` as `status="bad_trap"` and `finish_code=N`
- Existing `status`, `labels`, `notes`, and CLI exit semantics remain backward-compatible.
- Full local regression slice passes after the change.
