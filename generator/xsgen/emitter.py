from __future__ import annotations

from pathlib import Path

from generator.xsgen.model import ComposePlan


def descriptor_symbol(snippet_id: str) -> str:
    return f"snippet_{snippet_id}"


def emit_harness(plan: ComposePlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '#include "xsrt_env.h"',
        '#include "xs_snippet.h"',
        "",
    ]

    for snippet_id in plan.snippet_ids:
        lines.append(
            f"extern const xsrt_snippet_desc_t {descriptor_symbol(snippet_id)};"
        )

    lines.extend(
        [
            "",
            "int main(void) {",
            "  xsrt_env_t env;",
            "  int rc;",
            "",
            "  xsrt_init(&env);",
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
