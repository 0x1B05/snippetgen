from __future__ import annotations

from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from generator.xsgen.model import RunSeedArtifacts, TargetRunResult


RunTargetCallable = Callable[..., TargetRunResult]


def load_run_target(repo_root: Path, target: str) -> RunTargetCallable:
    module_path = repo_root / "targets" / target / "run_target.py"
    if not module_path.is_file():
        raise RuntimeError(f"run target adapter not found for target: {target}")

    spec = spec_from_file_location(f"xsgen_run_target_{target}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load run target adapter: {module_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    run_target = getattr(module, "run_target", None)
    if run_target is None:
        raise RuntimeError(f"run target adapter missing run_target(): {module_path}")
    return run_target
