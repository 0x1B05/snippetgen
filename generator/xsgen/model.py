from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SnippetSpec:
    id: str
    kind: str
    lang: str
    sources: tuple[Path, ...]


@dataclass(frozen=True)
class SuiteSpec:
    name: str
    target: str
    seed: int
    compose_mode: str
    snippet_ids: tuple[str, ...]


@dataclass(frozen=True)
class ComposePlan:
    suite_name: str
    target: str
    seed: int
    snippet_ids: tuple[str, ...]
    snippets: tuple[SnippetSpec, ...]


@dataclass(frozen=True)
class BuildArtifact:
    suite_name: str
    build_dir: Path
    elf_path: Path | None = None
    bin_path: Path | None = None
    build_manifest_path: Path | None = None
