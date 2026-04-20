# Scalar Misalign Phase 2 Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first Phase 2 scalar misalign matrix wave using `proc + check` snippets, covering load split templates, store split templates, and one cross-page permission suite, then run all three on XiangShan `emu`.

**Architecture:** Wave 1 introduces a shared `xs_scalar_misalign.h` debug contract plus three `proc + check` snippet pairs. The load/store matrix snippets stay purely software-visible and verify final merged values or byte fragments; the cross-page snippet reuses the existing `sv39`/`PMP` helpers pattern already proven by the `nexus_memscan_*` AM programs, but packages the result into the `proc + check` path with flags and debug CSR state.

**Tech Stack:** C11 snippets, shared snippet header, `xsrt_env`, `xsrt_trap`, existing XiangShan runner, Python `unittest`.

---

## File Map

- Create: `snippets/include/xs_scalar_misalign.h`
- Create: `snippets/scalar_misalign/load_split_templates.c`
- Create: `snippets/scalar_misalign/check_load_split_templates.c`
- Create: `snippets/scalar_misalign/store_split_templates.c`
- Create: `snippets/scalar_misalign/check_store_split_templates.c`
- Create: `snippets/scalar_misalign/cross_page_faults.c`
- Create: `snippets/scalar_misalign/check_cross_page_faults.c`
- Create: `snippets/manifests/load_split_templates.yaml`
- Create: `snippets/manifests/check_load_split_templates.yaml`
- Create: `snippets/manifests/store_split_templates.yaml`
- Create: `snippets/manifests/check_store_split_templates.yaml`
- Create: `snippets/manifests/cross_page_faults.yaml`
- Create: `snippets/manifests/check_cross_page_faults.yaml`
- Create: `suites/scalar_misalign_load_split_templates_poc.yaml`
- Create: `suites/scalar_misalign_store_split_templates_poc.yaml`
- Create: `suites/scalar_misalign_cross_page_faults_poc.yaml`
- Create: `docs/2026-04-20-scalar-misalign-phase2-wave1-run-notes.md`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_run_pipeline.py`

## Scope Rules

- Wave 1 does not include replay probe or seed-search suites.
- Wave 1 does not include a forwarding search upgrade of `misaligned_split_store_search`.
- The load/store split suites must not depend on trap handling.
- The cross-page suite may use trap handling, `satp`, and `PMP`, but must only assert software-visible fault cause and `tval`.

## Tasks

1. Add failing file/build-surface tests for the three new suites and the shared header.
2. Implement `xs_scalar_misalign.h` plus the load/store split template snippets and checks.
3. Implement the cross-page permission snippet and check, reusing the proven `sv39 + allow-all PMP baseline` approach.
4. Run the new local tests.
5. Run the three new suites on XiangShan `emu`.
6. Record run evidence in a notes doc.

## Acceptance Criteria

- `xs_scalar_misalign.h` defines one shared debug CSR/flag contract for Wave 1.
- `scalar_misalign_load_split_templates_poc` builds and reaches `good_trap`.
- `scalar_misalign_store_split_templates_poc` builds and reaches `good_trap`.
- `scalar_misalign_cross_page_faults_poc` builds and reaches `good_trap`.
- Local test coverage exists for file presence and build surface of all three suites.
- Real-run evidence is recorded in `docs/2026-04-20-scalar-misalign-phase2-wave1-run-notes.md`.
