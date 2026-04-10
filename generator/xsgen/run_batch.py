from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import json

from generator.xsgen.emitter import emit_harness
from generator.xsgen.model import RunEntry, RunLedger, RunSeedArtifacts, TargetRunResult
from generator.xsgen.run_target import load_run_target
from generator.xsgen.snippet_db import load_snippet_db
from generator.xsgen.suite_loader import build_compose_plan, load_suite
from generator.xsgen.toolchain import artifact_paths_for_run_seed, build_artifacts


def normalize_seeds(
    *,
    seed: int | None,
    seeds: str | None,
    seed_range: str | None,
) -> tuple[int, ...]:
    provided = [value is not None for value in (seed, seeds, seed_range)]
    if sum(provided) != 1:
        raise ValueError("exactly one seed selector must be provided")

    if seed is not None:
        return (seed,)

    if seeds is not None:
        parts = seeds.split(",")
        if not parts:
            raise ValueError("invalid seed list")
        values: list[int] = []
        seen: set[int] = set()
        for part in parts:
            if not part.strip():
                raise ValueError("invalid seed list contains an empty seed")
            try:
                value = int(part)
            except ValueError as exc:
                raise ValueError(f"invalid seed value: {part}") from exc
            if value in seen:
                raise ValueError(f"duplicate seed value: {value}")
            seen.add(value)
            values.append(value)
        return tuple(values)

    assert seed_range is not None
    bounds = seed_range.split(":")
    if len(bounds) != 2 or not bounds[0] or not bounds[1]:
        raise ValueError(f"invalid seed range: {seed_range}")
    try:
        start = int(bounds[0])
        end = int(bounds[1])
    except ValueError as exc:
        raise ValueError(f"invalid seed range: {seed_range}") from exc
    if end < start:
        raise ValueError(f"invalid seed range: {seed_range}")
    return tuple(range(start, end + 1))


def _default_run_batch_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")


def _ensure_log_files(stdout_log_path: Path, stderr_log_path: Path) -> None:
    stdout_log_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_log_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_log_path.touch(exist_ok=True)
    stderr_log_path.touch(exist_ok=True)


def _entry_payload(entry: RunEntry) -> dict:
    return {
        "suite": entry.suite_name,
        "target": entry.target,
        "run_batch": entry.run_batch,
        "seed": entry.seed,
        "artifact_dir": str(entry.artifact_dir),
        "elf": str(entry.elf_path),
        "bin": str(entry.bin_path),
        "stdout_log": str(entry.stdout_log_path),
        "stderr_log": str(entry.stderr_log_path),
        "run_meta": str(entry.run_meta_path),
        "status": entry.status,
        "labels": list(entry.labels),
        "notes": entry.notes,
        "returncode": entry.returncode,
    }


def _write_run_meta(entry: RunEntry) -> None:
    entry.run_meta_path.write_text(json.dumps(_entry_payload(entry), indent=2, sort_keys=True))


def _write_run_ledger(
    *,
    suite_name: str,
    target: str,
    run_batch: str,
    entries: list[RunEntry],
    ledger_path: Path,
) -> Path:
    ledger = RunLedger(
        suite_name=suite_name,
        target=target,
        run_batch=run_batch,
        entries=tuple(entries),
    )
    payload = {
        "suite": ledger.suite_name,
        "target": ledger.target,
        "run_batch": ledger.run_batch,
        "entries": [_entry_payload(entry) for entry in ledger.entries],
    }
    ledger_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return ledger_path


def run_suite_batch(
    *,
    repo_root: Path,
    suite_path: Path,
    seed_values: tuple[int, ...],
    target_loader=load_run_target,
    run_batch_id: str | None = None,
    timeout_s: int | None = None,
) -> Path:
    snippet_db = load_snippet_db(repo_root)
    base_suite = load_suite(suite_path)
    run_batch = run_batch_id or _default_run_batch_id()
    ledger_path = (repo_root / "build" / base_suite.name / "runs" / run_batch / "run_ledger.json").resolve()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    target_runner = target_loader(repo_root, base_suite.target)
    entries: list[RunEntry] = []

    for seed in seed_values:
        suite = replace(base_suite, seed=seed)
        plan = build_compose_plan(suite, snippet_db)
        artifact = artifact_paths_for_run_seed(repo_root, plan.suite_name, run_batch, seed)
        stdout_log_path = artifact.build_dir / "stdout.log"
        stderr_log_path = artifact.build_dir / "stderr.log"
        run_meta_path = artifact.build_dir / "run_meta.json"
        _ensure_log_files(stdout_log_path, stderr_log_path)

        try:
            emit_harness(plan, artifact.generated_suite_path)
            build_artifacts(repo_root, plan, artifact)
            run_artifacts = RunSeedArtifacts(
                suite_name=plan.suite_name,
                target=plan.target,
                seed=seed,
                run_batch=run_batch,
                build_artifact=artifact,
                stdout_log_path=stdout_log_path,
                stderr_log_path=stderr_log_path,
                run_meta_path=run_meta_path,
            )
            target_result = target_runner(artifacts=run_artifacts, timeout_s=timeout_s)
        except Exception as exc:
            stderr_log_path.write_text(f"{exc}\n")
            target_result = TargetRunResult(
                status="error",
                labels=("error",),
                notes=str(exc),
                returncode=None,
            )

        entry = RunEntry(
            suite_name=plan.suite_name,
            target=plan.target,
            run_batch=run_batch,
            seed=seed,
            artifact_dir=artifact.build_dir,
            elf_path=artifact.elf_path,
            bin_path=artifact.bin_path,
            stdout_log_path=stdout_log_path,
            stderr_log_path=stderr_log_path,
            run_meta_path=run_meta_path,
            status=target_result.status,
            labels=target_result.labels,
            notes=target_result.notes,
            returncode=target_result.returncode,
        )
        _write_run_meta(entry)
        entries.append(entry)

    return _write_run_ledger(
        suite_name=base_suite.name,
        target=base_suite.target,
        run_batch=run_batch,
        entries=entries,
        ledger_path=ledger_path,
    )
