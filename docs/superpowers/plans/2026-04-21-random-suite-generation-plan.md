# Random Suite Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-pass random deferred-check suite generator for the built-in `scalar_misalign_full` pool.

**Architecture:** Introduce a dedicated suite-generation module with built-in pools and a deterministic RNG path. Wire it into the CLI, test the generated YAML/build flow, then generate real suites and validate them on XiangShan `emu`.

**Tech Stack:** Python 3, `argparse`, `yaml`, `unittest`, XiangShan `emu`.

---

## File Map

- Create: `generator/xsgen/suite_generator.py`
- Modify: `generator/cli.py`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Create: `docs/superpowers/specs/2026-04-21-random-suite-generation-design.md`
- Create: `docs/2026-04-21-random-suite-generation-run-notes.md`
- Create: `docs/evidence/random-suite-generation/`

## Tasks

### Task 1: Add built-in pool generator and CLI
- [ ] Implement built-in suite pools
- [ ] Add `list-suite-pools`
- [ ] Add `generate-suites`

### Task 2: Add tests
- [ ] Verify CLI lists `scalar_misalign_full`
- [ ] Verify generated suite batch JSON and YAML structure
- [ ] Verify a generated suite builds successfully

### Task 3: Generate concrete suites and run them on emu
- [ ] Generate a recorded batch under `docs/evidence/random-suite-generation/generated_suites`
- [ ] Run all generated suites on XiangShan `emu`
- [ ] Copy resulting `batch_meta.json` files into `docs/evidence/random-suite-generation/`

### Task 4: Final verification
- [ ] Run `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline tests.test_run_pipeline -v`
