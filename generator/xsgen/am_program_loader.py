from __future__ import annotations

from pathlib import Path
import re


ENTRY_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_am_program_entry(data: dict, path: Path) -> str:
    entry = data.get("entry", "main")
    if not isinstance(entry, str) or not entry:
        raise ValueError(f"{path} field 'entry' must be a non-empty string")
    if ENTRY_SYMBOL_RE.fullmatch(entry) is None:
        raise ValueError(f"{path} invalid AM program entry symbol: {entry}")
    return entry
