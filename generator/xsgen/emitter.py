from __future__ import annotations

from pathlib import Path

from generator.xsgen.model import ComposePlan
from generator.xsgen.program_harness import emit_program_wrapper


def descriptor_symbol(snippet_id: str) -> str:
    return f"snippet_{snippet_id}"


def format_seed_literal(seed: int) -> str:
    return f"0x{seed:x}ull"


def emit_harness(plan: ComposePlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '#include "xsrt_env.h"',
        '#include "xs_snippet.h"',
        "",
    ]

    emitted_wrappers: set[str] = set()
    for snippet in plan.snippets:
        if snippet.id in emitted_wrappers:
            continue
        if snippet.kind == "am_program":
            if '#include "xsam/program_snippet.h"' not in lines:
                lines.insert(2, '#include "xsam/program_snippet.h"')
            lines.extend(emit_program_wrapper(snippet))
        else:
            lines.append(
                f"extern const xsrt_snippet_desc_t {descriptor_symbol(snippet.id)};"
            )
        emitted_wrappers.add(snippet.id)

    lines.extend(
        [
            "",
            "int main(void) {",
            "  xsrt_env_t env;",
            "  int rc;",
            "",
            "  xsrt_init(&env);",
            f"  env.seed = {format_seed_literal(plan.seed)};",
            "",
        ]
    )

    for snippet_id in plan.snippet_ids:
        symbol = descriptor_symbol(snippet_id)
        lines.extend(
            [
                f"  rc = xsrt_run_snippet(&env, &{symbol});",
                "  if (rc != 0) {",
                "    xsrt_finish_fail(&env, (unsigned long) rc);",
                "    return rc;",
                "  }",
                "",
            ]
        )

    lines.extend(
        [
            "  xsrt_finish_pass(&env);",
            "  return 0;",
            "}",
            "",
        ]
    )

    output_path.write_text("\n".join(lines))
    return output_path
