from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess

from generator.xsgen.model import TargetRunResult


DEFAULT_MAX_INSTR = 20000
DEFAULT_TIMEOUT_SEC = 15


def _emu_path() -> Path | None:
    override = os.environ.get("SNIPPETGEN_XS_EMU")
    if override:
        return Path(override)

    found = shutil.which("emu")
    if found is None:
        return None
    return Path(found)


def _error_result(*, artifacts, notes: str, labels: tuple[str, ...] = ("error",)) -> TargetRunResult:
    artifacts.stderr_log_path.write_text(f"{notes}\n")
    artifacts.stdout_log_path.write_text("")
    return TargetRunResult(
        status="error",
        labels=labels,
        notes=notes,
        returncode=None,
    )


def run_target(*, artifacts, timeout_s: int | None) -> TargetRunResult:
    emu_path = _emu_path()
    if artifacts.build_artifact.bin_path is None or not artifacts.build_artifact.bin_path.is_file():
        return _error_result(artifacts=artifacts, notes="missing bin artifact")

    if emu_path is None:
        return _error_result(
            artifacts=artifacts,
            notes="runner missing: emu",
            labels=("error", "runner_missing"),
        )

    if not emu_path.is_file():
        return _error_result(
            artifacts=artifacts,
            notes=f"runner missing: {emu_path}",
            labels=("error", "runner_missing"),
        )

    timeout_value = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_SEC
    max_instr = int(os.environ.get("SNIPPETGEN_RUN_MAX_INSTR", str(DEFAULT_MAX_INSTR)))
    command = [
        str(emu_path),
        "--no-diff",
        "-s",
        str(artifacts.seed),
        "-I",
        str(max_instr),
        "-i",
        str(artifacts.build_artifact.bin_path),
        "--force-dump-result",
    ]

    with artifacts.stdout_log_path.open("w") as stdout_file, artifacts.stderr_log_path.open("w") as stderr_file:
        try:
            result = subprocess.run(
                command,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                timeout=timeout_value,
            )
        except subprocess.TimeoutExpired:
            with artifacts.stderr_log_path.open("a") as stderr_append:
                stderr_append.write(f"timeout after {timeout_value}s\n")
            return TargetRunResult(
                status="timeout",
                labels=("built", "timeout"),
                notes=f"timeout after {timeout_value}s",
                returncode=None,
            )

    if result.returncode == 0:
        return TargetRunResult(
            status="ran",
            labels=("built", "ran"),
            notes="",
            returncode=0,
        )

    return TargetRunResult(
        status="nonzero_exit",
        labels=("built", "ran", "nonzero_exit"),
        notes=f"runner exited with code {result.returncode}",
        returncode=result.returncode,
    )
