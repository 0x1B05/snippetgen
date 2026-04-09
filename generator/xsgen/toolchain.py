from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess

from generator.xsgen.model import BuildArtifact, ComposePlan


def artifact_paths_for_suite(repo_root: Path, suite_name: str) -> BuildArtifact:
    build_dir = (repo_root / "build" / suite_name).resolve()
    return BuildArtifact(
        suite_name=suite_name,
        build_dir=build_dir,
        generated_suite_path=build_dir / "generated_suite.c",
        elf_path=build_dir / "test.elf",
        bin_path=build_dir / "test.bin",
        build_manifest_path=build_dir / "build_manifest.json",
    )


def _find_tool(name: str) -> str | None:
    override = os.environ.get(name)
    if override:
        return override
    return shutil.which(name)


def detect_toolchain() -> dict[str, str]:
    candidates = (
        "riscv64-unknown-linux-gnu",
        "riscv64-unknown-elf",
        "riscv64-linux-gnu",
    )

    for prefix in candidates:
        gcc = _find_tool(f"{prefix}-gcc")
        objcopy = _find_tool(f"{prefix}-objcopy")
        if gcc and objcopy:
            return {"prefix": prefix, "gcc": gcc, "objcopy": objcopy}

    raise RuntimeError("RISC-V cross toolchain not found")


def runtime_sources(repo_root: Path) -> list[Path]:
    return [
        repo_root / "runtime" / "arch" / "riscv64" / "start.S",
        repo_root / "runtime" / "arch" / "riscv64" / "trap.S",
        repo_root / "runtime" / "src" / "xsrt_env.c",
        repo_root / "runtime" / "src" / "xsrt_csr.c",
        repo_root / "runtime" / "src" / "xsrt_trap.c",
        repo_root / "runtime" / "src" / "xsrt_intr.c",
        repo_root / "runtime" / "src" / "xsrt_snippet.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsrt_platform.c",
    ]


def build_artifacts(
    repo_root: Path,
    plan: ComposePlan,
    artifact: BuildArtifact,
) -> BuildArtifact:
    toolchain = detect_toolchain()
    artifact.build_dir.mkdir(parents=True, exist_ok=True)

    compile_cmd = [
        toolchain["gcc"],
        "-march=rv64gc",
        "-mabi=lp64d",
        "-mcmodel=medany",
        "-ffreestanding",
        "-nostdlib",
        "-nostartfiles",
        "-static",
        "-Wl,-e,_start",
        "-Wl,-Ttext=0x80000000",
        "-I",
        str((repo_root / "runtime" / "include").resolve()),
        "-I",
        str((repo_root / "snippets" / "include").resolve()),
        "-I",
        str((repo_root / "runtime" / "platform" / "xiangshan").resolve()),
        "-o",
        str(artifact.elf_path),
    ]
    compile_cmd.extend(str(path.resolve()) for path in runtime_sources(repo_root))
    for snippet in plan.snippets:
        compile_cmd.extend(str(source) for source in snippet.sources)
    compile_cmd.append(str(artifact.generated_suite_path))

    compile_result = subprocess.run(
        compile_cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if compile_result.returncode != 0:
        raise RuntimeError(compile_result.stderr or "RISC-V compile/link failed")

    objcopy_cmd = [
        toolchain["objcopy"],
        "-O",
        "binary",
        str(artifact.elf_path),
        str(artifact.bin_path),
    ]
    try:
        objcopy_result = subprocess.run(
            objcopy_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"objcopy failed: {objcopy_cmd[0]}") from exc
    if objcopy_result.returncode != 0:
        raise RuntimeError(objcopy_result.stderr or "RISC-V objcopy failed")

    manifest_payload = {
        "suite": plan.suite_name,
        "target": plan.target,
        "seed": plan.seed,
        "snippet_ids": list(plan.snippet_ids),
        "sources": [str(source) for snippet in plan.snippets for source in snippet.sources],
        "artifacts": {
            "build_dir": str(artifact.build_dir),
            "generated_suite": str(artifact.generated_suite_path),
            "elf": str(artifact.elf_path),
            "bin": str(artifact.bin_path),
            "build_manifest": str(artifact.build_manifest_path),
        },
        "commands": {
            "compile": compile_cmd,
            "objcopy": objcopy_cmd,
        },
    }
    artifact.build_manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True))
    return artifact
