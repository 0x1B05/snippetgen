from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess

from generator.xsgen.model import BuildArtifact, ComposePlan


def _artifact_paths_for_build_dir(build_dir: Path, suite_name: str) -> BuildArtifact:
    build_dir = build_dir.resolve()
    return BuildArtifact(
        suite_name=suite_name,
        build_dir=build_dir,
        generated_suite_path=build_dir / "generated_suite.c",
        elf_path=build_dir / "test.elf",
        bin_path=build_dir / "test.bin",
        disasm_path=build_dir / "disasm",
        build_manifest_path=build_dir / "build_manifest.json",
    )


def artifact_paths_for_suite(repo_root: Path, suite_name: str) -> BuildArtifact:
    return _artifact_paths_for_build_dir(repo_root / "build" / suite_name, suite_name)


def artifact_paths_for_run_seed(
    repo_root: Path,
    suite_name: str,
    run_batch: str,
    seed: int,
) -> BuildArtifact:
    build_dir = repo_root / "build" / suite_name / "runs" / run_batch / f"seed_{seed}"
    return _artifact_paths_for_build_dir(build_dir, suite_name)


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


def resolve_objdump(toolchain: dict[str, str]) -> str:
    if "objdump" in toolchain and toolchain["objdump"]:
        return toolchain["objdump"]

    objdump_name = f'{toolchain["prefix"]}-objdump'

    for anchor in ("gcc", "objcopy"):
        candidate = Path(toolchain[anchor]).with_name(objdump_name)
        if candidate.is_file():
            return str(candidate)

    found = _find_tool(objdump_name)
    if found is not None:
        return found

    raise RuntimeError(f"RISC-V objdump not found: {objdump_name}")


def runtime_sources(repo_root: Path) -> list[Path]:
    return [
        repo_root / "runtime" / "arch" / "riscv64" / "start.S",
        repo_root / "runtime" / "arch" / "riscv64" / "trap.S",
        repo_root / "runtime" / "src" / "xsrt_env.c",
        repo_root / "runtime" / "src" / "xsrt_csr.c",
        repo_root / "runtime" / "src" / "xsrt_trap.c",
        repo_root / "runtime" / "src" / "xsrt_intr.c",
        repo_root / "runtime" / "src" / "xsrt_snippet.c",
        repo_root / "runtime" / "src" / "xsam_trm.c",
        repo_root / "runtime" / "src" / "xsam_cte.c",
        repo_root / "runtime" / "src" / "xsam_vme.c",
        repo_root / "runtime" / "src" / "xsam_ioe.c",
        repo_root / "runtime" / "src" / "xsam_program_snippet.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsam_xs_clint.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsam_xs_plic.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsam_xs_pma.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsam_xs_pmp.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsam_xs_cache.c",
        repo_root / "runtime" / "platform" / "xiangshan" / "xsrt_platform.c",
    ]


def runtime_linker_script(repo_root: Path) -> Path:
    return (repo_root / "runtime" / "platform" / "xiangshan" / "section.ld").resolve()


def unique_plan_sources(plan: ComposePlan) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []

    for snippet in plan.snippets:
        sources = snippet.sources[1:] if snippet.kind == "am_program" else snippet.sources
        for source_path in sources:
            if source_path in seen:
                continue
            seen.add(source_path)
            ordered.append(source_path)

    return ordered


def build_artifacts(
    repo_root: Path,
    plan: ComposePlan,
    artifact: BuildArtifact,
) -> BuildArtifact:
    compile_flags = [
        "-O2",
        "-march=rv64gcv_zicbop",
        "-mabi=lp64d",
        "-mcmodel=medany",
        "-ffreestanding",
        "-fno-asynchronous-unwind-tables",
        "-fno-builtin",
        "-fno-stack-protector",
        "-fno-tree-vectorize",
        "-fno-tree-slp-vectorize",
    ]
    include_flags = [
        "-I",
        str((repo_root / "runtime" / "include").resolve()),
        "-I",
        str((repo_root / "snippets" / "include").resolve()),
        "-I",
        str((repo_root / "runtime" / "platform" / "xiangshan").resolve()),
    ]
    toolchain = detect_toolchain()
    object_dir = artifact.build_dir / "obj"
    compile_commands: list[list[str]] = []
    object_paths: list[str] = []

    artifact.build_dir.mkdir(parents=True, exist_ok=True)
    if object_dir.exists():
        shutil.rmtree(object_dir)
    object_dir.mkdir(parents=True, exist_ok=True)

    for path in (artifact.elf_path, artifact.bin_path, artifact.disasm_path, artifact.build_manifest_path):
        if path.exists():
            path.unlink()

    for index, source_path in enumerate(runtime_sources(repo_root), start=1):
        object_path = object_dir / f"{index:02d}_{source_path.stem}.o"
        object_dir.mkdir(parents=True, exist_ok=True)
        compile_cmd = [
            toolchain["gcc"],
            *compile_flags,
            *include_flags,
            "-c",
            str(source_path.resolve()),
            "-o",
            str(object_path),
        ]
        compile_result = subprocess.run(
            compile_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        compile_commands.append(compile_cmd)
        if compile_result.returncode != 0:
            raise RuntimeError(compile_result.stderr or "RISC-V compile failed")
        object_paths.append(str(object_path))

    source_index = len(object_paths) + 1
    for source_path in unique_plan_sources(plan):
        object_path = object_dir / f"{source_index:02d}_{source_path.stem}.o"
        object_dir.mkdir(parents=True, exist_ok=True)
        compile_cmd = [
            toolchain["gcc"],
            *compile_flags,
            *include_flags,
            "-c",
            str(source_path),
            "-o",
            str(object_path),
        ]
        compile_result = subprocess.run(
            compile_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        compile_commands.append(compile_cmd)
        if compile_result.returncode != 0:
            raise RuntimeError(compile_result.stderr or "RISC-V compile failed")
        object_paths.append(str(object_path))
        source_index += 1

    generated_object = object_dir / f"{source_index:02d}_{artifact.generated_suite_path.stem}.o"
    object_dir.mkdir(parents=True, exist_ok=True)
    generated_compile_cmd = [
        toolchain["gcc"],
        *compile_flags,
        *include_flags,
        "-c",
        str(artifact.generated_suite_path),
        "-o",
        str(generated_object),
    ]
    generated_compile_result = subprocess.run(
        generated_compile_cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    compile_commands.append(generated_compile_cmd)
    if generated_compile_result.returncode != 0:
        raise RuntimeError(generated_compile_result.stderr or "RISC-V compile failed")
    object_paths.append(str(generated_object))

    link_cmd = [
        toolchain["gcc"],
        *compile_flags,
        "-nostdlib",
        "-nostartfiles",
        "-static",
        f"-Wl,-T{runtime_linker_script(repo_root)}",
        "-o",
        str(artifact.elf_path),
    ]
    link_cmd.extend(object_paths)

    link_result = subprocess.run(
        link_cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if link_result.returncode != 0:
        for path in (artifact.elf_path, artifact.bin_path, artifact.build_manifest_path):
            if path.exists():
                path.unlink()
        raise RuntimeError(link_result.stderr or "RISC-V link failed")

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
        for path in (artifact.elf_path, artifact.bin_path, artifact.build_manifest_path):
            if path.exists():
                path.unlink()
        raise RuntimeError(f"objcopy failed: {objcopy_cmd[0]}") from exc
    if objcopy_result.returncode != 0:
        for path in (artifact.elf_path, artifact.bin_path, artifact.disasm_path, artifact.build_manifest_path):
            if path.exists():
                path.unlink()
        raise RuntimeError(objcopy_result.stderr or "RISC-V objcopy failed")

    objdump_cmd = [
        resolve_objdump(toolchain),
        "-d",
        str(artifact.elf_path),
    ]
    objdump_result = subprocess.run(
        objdump_cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if objdump_result.returncode != 0:
        for path in (artifact.elf_path, artifact.bin_path, artifact.disasm_path, artifact.build_manifest_path):
            if path.exists():
                path.unlink()
        raise RuntimeError(objdump_result.stderr or "RISC-V objdump failed")
    artifact.disasm_path.write_text(objdump_result.stdout)

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
            "disasm": str(artifact.disasm_path),
            "build_manifest": str(artifact.build_manifest_path),
        },
        "commands": {
            "compile": compile_commands,
            "link": link_cmd,
            "objcopy": objcopy_cmd,
            "objdump": objdump_cmd,
        },
    }
    artifact.build_manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True))
    return artifact
