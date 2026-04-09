#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.xsgen.snippet_db import load_snippet_db
from generator.xsgen.suite_loader import build_compose_plan, load_suite
from generator.xsgen.emitter import emit_harness
from generator.xsgen.toolchain import artifact_paths_for_suite, build_artifacts


def cmd_list_snippets(_: argparse.Namespace) -> int:
    snippet_db = load_snippet_db(REPO_ROOT)
    for snippet_id in sorted(snippet_db):
        print(snippet_id)
    return 0


def cmd_dump_plan(args: argparse.Namespace) -> int:
    snippet_db = load_snippet_db(REPO_ROOT)
    suite = load_suite(REPO_ROOT / args.suite)
    plan = build_compose_plan(suite, snippet_db)
    artifact = artifact_paths_for_suite(REPO_ROOT, plan.suite_name)
    payload = {
        "suite": plan.suite_name,
        "target": plan.target,
        "seed": plan.seed,
        "snippet_ids": list(plan.snippet_ids),
        "artifacts": {
            "build_dir": str(artifact.build_dir),
            "generated_suite": str(artifact.generated_suite_path),
            "elf": str(artifact.elf_path),
            "bin": str(artifact.bin_path),
            "build_manifest": str(artifact.build_manifest_path),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    snippet_db = load_snippet_db(REPO_ROOT)
    suite = load_suite(REPO_ROOT / args.suite)
    plan = build_compose_plan(suite, snippet_db)
    artifact = artifact_paths_for_suite(REPO_ROOT, plan.suite_name)
    emit_harness(plan, artifact.generated_suite_path)
    build_artifacts(REPO_ROOT, plan, artifact)
    print(artifact.build_manifest_path)
    return 0


def cmd_run(_: argparse.Namespace) -> int:
    raise SystemExit("run not implemented yet: target execution lands in a later round")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="snippetgen")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-snippets")
    list_parser.set_defaults(handler=cmd_list_snippets)

    dump_parser = subparsers.add_parser("dump-plan")
    dump_parser.add_argument("suite")
    dump_parser.set_defaults(handler=cmd_dump_plan)

    build_parser_cmd = subparsers.add_parser("build")
    build_parser_cmd.add_argument("suite", nargs="?")
    build_parser_cmd.set_defaults(handler=cmd_build)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("artifact", nargs="?")
    run_parser.set_defaults(handler=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
