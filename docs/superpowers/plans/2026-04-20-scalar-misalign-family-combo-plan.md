# Scalar Misalign Family Combo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic scalar-misalign family-combo suites that can mix existing proc/check snippets under deferred-check execution and validate them on real XiangShan `emu`.

**Architecture:** Lightly retrofit the existing deterministic scalar-misalign snippets so each one writes an isolated summary CSR instead of relying on shared state like `env->snippet_id`. Then add three deferred-check family suites, strengthen loading/build coverage, and run each suite on real `emu`.

**Tech Stack:** Python 3, `unittest`, freestanding C snippets, deferred-check suite schema, XiangShan `emu`.

---

## File Map

- Modify: `snippets/include/xs_scalar_misalign.h`
- Modify: `snippets/scalar_misalign/load_split_templates.c`
- Modify: `snippets/scalar_misalign/check_load_split_templates.c`
- Modify: `snippets/scalar_misalign/store_split_templates.c`
- Modify: `snippets/scalar_misalign/check_store_split_templates.c`
- Modify: `snippets/scalar_misalign/store_forward_overlap.c`
- Modify: `snippets/scalar_misalign/check_store_forward_overlap.c`
- Modify: `snippets/scalar_misalign/cross_page_faults.c`
- Modify: `snippets/scalar_misalign/check_cross_page_faults.c`
- Create: `suites/scalar_misalign_templates_combo_poc.yaml`
- Create: `suites/scalar_misalign_fault_forward_combo_poc.yaml`
- Create: `suites/scalar_misalign_family_combo_poc.yaml`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Create: `docs/2026-04-20-scalar-misalign-family-combo-run-notes.md`

## Tasks

### Task 1: Retrofit deterministic scalar-misalign snippets for family mixing

- [ ] Add isolated summary CSR ids to `xs_scalar_misalign.h`
- [ ] Update `load_split_templates` and `check_load_split_templates`
- [ ] Update `store_split_templates` and `check_store_split_templates`
- [ ] Update `store_forward_overlap` and `check_store_forward_overlap`
- [ ] Update `cross_page_faults` and `check_cross_page_faults`
- [ ] Run targeted compile/build regressions for the four existing standalone suites

### Task 2: Add deterministic family-combo suites and automated coverage

- [ ] Add the three new suite YAML files
- [ ] Add suite existence and deterministic-plan coverage in `tests/test_snippet_loading.py`
- [ ] Add build coverage in `tests/test_build_pipeline.py`
- [ ] Run focused loading/build tests and confirm green

### Task 3: Run real `emu` and capture evidence

- [ ] Run `scalar_misalign_templates_combo_poc` on `emu`
- [ ] Run `scalar_misalign_fault_forward_combo_poc` on `emu`
- [ ] Run `scalar_misalign_family_combo_poc` on `emu`
- [ ] Record `good_trap + finish_code=0` evidence in run notes

### Task 4: Final verification and commit

- [ ] Run `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline tests.test_run_pipeline -v`
- [ ] Commit the family-combo implementation
