from __future__ import annotations

from generator.xsgen.model import SnippetSpec


def descriptor_symbol(snippet_id: str) -> str:
    return f"snippet_{snippet_id}"


def program_entry_symbol(snippet_id: str) -> str:
    return f"xsam_program_entry_{snippet_id}"


def emit_program_wrapper(snippet: SnippetSpec) -> list[str]:
    if snippet.kind != "am_program":
        raise ValueError(f"snippet is not an AM program: {snippet.id}")
    if snippet.entry is None:
        raise ValueError(f"AM program snippet missing entry symbol: {snippet.id}")
    if not snippet.sources:
        raise ValueError(f"AM program snippet has no sources: {snippet.id}")

    entry_source = snippet.sources[0]
    entry_symbol = program_entry_symbol(snippet.id)

    return [
        f"#define {snippet.entry} {entry_symbol}",
        f'#include "{entry_source}"',
        f"#undef {snippet.entry}",
        (
            f'XSAM_DEFINE_PROGRAM_SNIPPET({descriptor_symbol(snippet.id)}, '
            f'"{snippet.id}", {entry_symbol});'
        ),
        "",
    ]
