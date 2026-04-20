# Scalar Misalign Phase 2 Wave 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the deterministic overlap/forwarding scalar misalign suite for Phase 2 and run it on XiangShan `emu`.

**Architecture:** Wave 2 extends the shared `xs_scalar_misalign.h` contract with one overlap flag/magic pair and adds a single `proc + check` suite. The execution snippet constructs an older cross-16B store and verifies that multiple younger loads observe the complete value and high fragment, never a half-visible result; the check snippet only asserts the software-visible state recorded in flags, `snippet_id`, and shared debug CSR.

**Tech Stack:** C11 proc/check snippets, shared snippet header, XiangShan `emu`, Python `unittest`.

---

## File Map

- Modify: `snippets/include/xs_scalar_misalign.h`
- Create: `snippets/scalar_misalign/store_forward_overlap.c`
- Create: `snippets/scalar_misalign/check_store_forward_overlap.c`
- Create: `snippets/manifests/store_forward_overlap.yaml`
- Create: `snippets/manifests/check_store_forward_overlap.yaml`
- Create: `suites/scalar_misalign_store_forward_overlap_poc.yaml`
- Create: `docs/2026-04-20-scalar-misalign-phase2-wave2-run-notes.md`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`

## Acceptance Criteria

- The new overlap suite builds through `init_basic_env -> store_forward_overlap -> check_store_forward_overlap -> finish_check`.
- The execution snippet records entered/completed state in the shared header contract.
- The real `emu` run reaches `good_trap` with `finish_code=0`.
- Evidence is recorded in `docs/2026-04-20-scalar-misalign-phase2-wave2-run-notes.md`.
