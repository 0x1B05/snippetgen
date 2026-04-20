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

    legacy_present = "snippets" in compose
    deferred_present = "run_snippets" in compose or "check_snippets" in compose

    legacy_snippet_ids = compose.get("snippets")
    run_snippet_ids = compose.get("run_snippets")
    check_snippet_ids = compose.get("check_snippets")

    if legacy_present and deferred_present:
        raise ValueError(f"{path} cannot mix compose.snippets with run_snippets/check_snippets")

    if legacy_present:
        if not isinstance(legacy_snippet_ids, list) or not legacy_snippet_ids:
            raise ValueError(f"{path} field 'compose.snippets' must be a non-empty list")
        if not all(isinstance(item, str) and item for item in legacy_snippet_ids):
            raise ValueError(f"{path} field 'compose.snippets' contains an invalid snippet id")

        return SuiteSpec(
            name=suite_name,
            target=target,
            seed=raw_seed,
            compose_mode=str(mode),
            snippet_ids=tuple(legacy_snippet_ids),
        )

    if not deferred_present:
        raise ValueError(f"{path} compose section requires snippets or run_snippets/check_snippets")
    if not isinstance(run_snippet_ids, list) or not run_snippet_ids:
        raise ValueError(f"{path} field 'compose.run_snippets' must be a non-empty list")
    if not isinstance(check_snippet_ids, list) or not check_snippet_ids:
        raise ValueError(f"{path} field 'compose.check_snippets' must be a non-empty list")
    if not all(isinstance(item, str) and item for item in [*run_snippet_ids, *check_snippet_ids]):
        raise ValueError(f"{path} deferred compose contains an invalid snippet id")

    snippet_ids = tuple(dict.fromkeys([*run_snippet_ids, *check_snippet_ids]))

    return SuiteSpec(
        name=suite_name,
        target=target,
        seed=raw_seed,
        compose_mode=str(mode),
        snippet_ids=snippet_ids,
        run_snippet_ids=tuple(run_snippet_ids),
        check_snippet_ids=tuple(check_snippet_ids),
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
        run_snippet_ids=suite.run_snippet_ids,
        check_snippet_ids=suite.check_snippet_ids,
    )
