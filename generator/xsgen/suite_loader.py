from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
import re

import yaml

from generator.xsgen.model import ComposePlan, SnippetSpec, SuiteSpec

SUPPORTED_TARGET = "xiangshan-verilator"
SUITE_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


def _require_mapping(data: object, path: Path) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_suite(path: Path) -> SuiteSpec:
    data = _require_mapping(yaml.safe_load(path.read_text()), path)
    compose = _require_mapping(data.get("compose"), path)

    for field in ("suite", "target", "seed"):
        if field not in data:
            raise ValueError(f"{path} missing required field: {field}")

    suite_name = str(data["suite"])
    if SUITE_NAME_RE.fullmatch(suite_name) is None:
        raise ValueError(f"{path} invalid suite name: {suite_name}")

    raw_seed = data["seed"]
    if isinstance(raw_seed, bool) or not isinstance(raw_seed, int) or raw_seed < 0:
        raise ValueError(f"{path} invalid seed: {raw_seed}")

    target = str(data["target"])
    if target != SUPPORTED_TARGET:
        raise ValueError(f"{path} unsupported target: {target}")

    mode = compose.get("mode")
    if mode != "sequence":
        raise ValueError(f"{path} compose mode '{mode}' is future-only in ELF-first PoC")

    snippet_ids = compose.get("snippets")
    if not isinstance(snippet_ids, list) or not snippet_ids:
        raise ValueError(f"{path} field 'compose.snippets' must be a non-empty list")
    if not all(isinstance(item, str) and item for item in snippet_ids):
        raise ValueError(f"{path} field 'compose.snippets' contains an invalid snippet id")

    return SuiteSpec(
        name=suite_name,
        target=target,
        seed=raw_seed,
        compose_mode=str(mode),
        snippet_ids=tuple(snippet_ids),
    )


def build_compose_plan(
    suite: SuiteSpec,
    snippet_db: Mapping[str, SnippetSpec],
) -> ComposePlan:
    resolved_snippets: list[SnippetSpec] = []
    for snippet_id in suite.snippet_ids:
        if snippet_id not in snippet_db:
            raise ValueError(f"unknown snippet id in suite: {snippet_id}")
        resolved_snippets.append(snippet_db[snippet_id])

    return ComposePlan(
        suite_name=suite.name,
        target=suite.target,
        seed=suite.seed,
        snippet_ids=suite.snippet_ids,
        snippets=tuple(resolved_snippets),
    )
