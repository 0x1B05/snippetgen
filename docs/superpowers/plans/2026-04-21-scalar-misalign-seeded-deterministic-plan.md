# Scalar Misalign Seeded Deterministic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen deterministic scalar-misalign snippets with seed-driven parameterization while keeping strict pass/fail behavior.

**Architecture:** Encode seed-driven rounds/rotation/slot selection directly inside the four deterministic snippets and mirror those formulas in their checks. Then verify with source-contract tests, build regressions, full local buckets, and persistent real-emu evidence.

**Tech Stack:** freestanding C snippets, Python `unittest`, XiangShan `emu`, batch_meta evidence copies.

---

## File Map

- Modify: `snippets/scalar_misalign/load_split_templates.c`
- Modify: `snippets/scalar_misalign/check_load_split_templates.c`
- Modify: `snippets/scalar_misalign/store_split_templates.c`
- Modify: `snippets/scalar_misalign/check_store_split_templates.c`
- Modify: `snippets/scalar_misalign/store_forward_overlap.c`
- Modify: `snippets/scalar_misalign/check_store_forward_overlap.c`
- Modify: `snippets/scalar_misalign/cross_page_faults.c`
- Modify: `snippets/scalar_misalign/check_cross_page_faults.c`
- Modify: `tests/test_snippet_loading.py`
- Create: `docs/2026-04-21-scalar-misalign-seeded-deterministic-run-notes.md`
- Create: `docs/evidence/scalar-misalign-seeded-deterministic/*.json`

## Tasks

### Task 1: Seed-drive the four deterministic snippets
- [ ] Add rounds/rotation/bank/value helpers
- [ ] Keep strict pass/fail semantics
- [ ] Keep family combo compatibility

### Task 2: Add source-contract coverage
- [ ] Lock that each strengthened snippet and check consumes `env->seed`
- [ ] Re-run targeted build regressions

### Task 3: Run full local regression bucket
- [ ] `tests.test_runtime_surface`
- [ ] `tests.test_snippet_loading`
- [ ] `tests.test_build_pipeline`
- [ ] `tests.test_run_pipeline`

### Task 4: Capture persistent real-emu records
- [ ] Run 4 standalone deterministic suites on non-default seeds
- [ ] Run 3 family combo suites on non-default seeds
- [ ] Copy `batch_meta.json` to `docs/evidence/scalar-misalign-seeded-deterministic/`
- [ ] Write run notes
