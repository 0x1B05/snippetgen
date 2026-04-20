# Scalar Misalign Phase 3 Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first scalar misalign probe/search suites for forwarding, cross-page fault ownership, and replay-style software proxies, then run them on XiangShan `emu`.

**Architecture:** Phase 3 stays on the `proc + check` path and extends the existing `xs_scalar_misalign.h` contract with three probe families. Each probe suite is seed-driven but still pass/fail: the execution snippet records entered/completed state plus compact debug CSR evidence, and the check snippet only validates software-visible outcomes and shared debug state.

**Tech Stack:** C11 proc/check snippets, shared misalign header, XiangShan `emu`, Python `unittest`.

---

## File Map

- Modify: `snippets/include/xs_scalar_misalign.h`
- Create: `snippets/scalar_misalign/store_forward_search.c`
- Create: `snippets/scalar_misalign/check_store_forward_search.c`
- Create: `snippets/scalar_misalign/cross_page_fault_search.c`
- Create: `snippets/scalar_misalign/check_cross_page_fault_search.c`
- Create: `snippets/scalar_misalign/replay_probe.c`
- Create: `snippets/scalar_misalign/check_replay_probe.c`
- Create: `snippets/manifests/store_forward_search.yaml`
- Create: `snippets/manifests/check_store_forward_search.yaml`
- Create: `snippets/manifests/cross_page_fault_search.yaml`
- Create: `snippets/manifests/check_cross_page_fault_search.yaml`
- Create: `snippets/manifests/replay_probe.yaml`
- Create: `snippets/manifests/check_replay_probe.yaml`
- Create: `suites/scalar_misalign_store_forward_search_poc.yaml`
- Create: `suites/scalar_misalign_cross_page_fault_search_poc.yaml`
- Create: `suites/scalar_misalign_replay_probe_poc.yaml`
- Create: `docs/2026-04-20-scalar-misalign-phase3-run-notes.md`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`

## Acceptance Criteria

- The three Phase 3 probe suites exist, build, and have deterministic snippet order.
- `scalar_misalign_store_forward_search_poc` reaches `good_trap` on real `emu`.
- `scalar_misalign_cross_page_fault_search_poc` reaches `good_trap` on real `emu`.
- `scalar_misalign_replay_probe_poc` reaches `good_trap` on real `emu`.
- Probe evidence is recorded in `docs/2026-04-20-scalar-misalign-phase3-run-notes.md`.
