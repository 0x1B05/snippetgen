from __future__ import annotations

from pathlib import Path
import re

import yaml

from generator.xsgen.am_program_loader import load_am_program_entry
from generator.xsgen.model import SnippetSpec


REQUIRED_FIELDS = ("id", "kind", "lang", "sources")
SNIPPET_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SUPPORTED_LANGS = {"c", "asm"}
SUPPORTED_KINDS = {"proc", "am_program"}


def _require_mapping(data: object, path: Path) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_manifest(path: Path, repo_root: Path) -> SnippetSpec:
    data = _require_mapping(yaml.safe_load(path.read_text()), path)

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"{path} missing required fields: {', '.join(missing)}")

    snippet_id = data["id"]
    kind = data["kind"]
    lang = data["lang"]
    raw_sources = data["sources"]

    if not isinstance(snippet_id, str) or not snippet_id:
        raise ValueError(f"{path} field 'id' must be a non-empty string")
    if SNIPPET_ID_RE.fullmatch(snippet_id) is None:
        raise ValueError(f"{path} invalid snippet id: {snippet_id}")
    if kind not in SUPPORTED_KINDS:
        raise ValueError(f"{path} kind '{kind}' not implemented in ELF-first PoC")
    if not isinstance(lang, str) or not lang:
        raise ValueError(f"{path} field 'lang' must be a non-empty string")
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f"{path} unsupported snippet language: {lang}")
    if kind == "am_program" and lang != "c":
        raise ValueError(f"{path} AM program snippets currently require lang: c")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError(f"{path} field 'sources' must be a non-empty list")

    resolved_sources: list[Path] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, str) or not raw_source:
            raise ValueError(f"{path} contains an invalid source entry: {raw_source!r}")
        resolved = (repo_root / raw_source).resolve()
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(f"{path} source escapes repository root: {raw_source}") from exc
        if not resolved.is_file():
            raise ValueError(f"{path} source does not exist: {raw_source}")
        resolved_sources.append(resolved)

    entry = None
    if kind == "am_program":
        entry = load_am_program_entry(data, path)

    return SnippetSpec(
        id=snippet_id,
        kind=kind,
        lang=lang,
        sources=tuple(resolved_sources),
        entry=entry,
    )


def load_snippet_db(repo_root: Path) -> dict[str, SnippetSpec]:
    manifest_dir = repo_root / "snippets" / "manifests"
    snippet_db: dict[str, SnippetSpec] = {}

    for manifest_path in sorted(manifest_dir.glob("*.yaml")):
        snippet = load_manifest(manifest_path, repo_root)
        if snippet.id in snippet_db:
            raise ValueError(f"duplicate snippet id: {snippet.id}")
        snippet_db[snippet.id] = snippet

    return snippet_db
