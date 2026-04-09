# Round 5 Summary

## Mainline Objective
- Keep the first-stage ELF-first build path faithful to the configured suite inputs and review contract by fixing the remaining review findings without widening scope beyond the accepted PoC contract.

## Blocking Issues Fixed
- Fixed the reviewed harness seed-propagation bug in `generator/xsgen/emitter.py`.
- Declared the `PyYAML` runtime dependency in `requirements.txt`.
- Rejected unsupported snippet languages during manifest loading in `generator/xsgen/snippet_db.py`.
- Deduplicated compiled snippet sources in `generator/xsgen/toolchain.py` so repeated snippet references no longer cause duplicate-definition link failures.
- Updated `runtime/arch/riscv64/start.S` so `_start` now transfers control to `main` with a minimal boot stack instead of returning immediately.
- Updated `snippets/scalar_load_legality/unaligned_load.c` so the RISC-V path emits a real misaligned `lw` instead of reconstructing the word from byte loads in software.
- Tightened `generator/xsgen/suite_loader.py` so negative, floating-point, and boolean seeds are rejected during suite loading instead of slipping into later build stages.

## Queued Follow-Up
- Left the `compose.ops` vs `compose.snippets` documentation mismatch queued.
- Left the same-suite concurrent build race under `build/<suite>/obj` queued.

## Resolution Details
- Added a regression test in `tests/test_build_pipeline.py` that creates a temporary suite with `seed: 99` and asserts the generated harness writes that non-default seed into `env.seed` after `xsrt_init(&env);` and before snippet execution.
- Updated `generator/xsgen/emitter.py` so harness emission formats `plan.seed` as a deterministic 64-bit literal and assigns it into `env.seed` before any snippet runs.
- Updated the existing harness-order test to assert the emitted default-suite seed literal in its new normalized form.
- Added `requirements.txt` with `PyYAML>=6.0` so the CLI's YAML loader dependency is declared in-repo.
- Added a manifest-loader regression in `tests/test_snippet_loading.py` for unsupported `lang` values and implemented `SUPPORTED_LANGS` validation in `generator/xsgen/snippet_db.py`.
- Added a build-path regression in `tests/test_build_pipeline.py` for repeated snippet references and implemented source deduplication in `generator/xsgen/toolchain.py` so each translation unit is compiled once per build.
- Added a runtime-surface regression that requires `_start` to reference `main` and transfer control instead of returning immediately.
- Added a snippet-loading regression that requires non-integer or negative seeds to be rejected during suite loading.
- Added a snippet-loading regression that requires the RISC-V path in `unaligned_load.c` to contain a real `lw`-based misaligned load.
- Updated `runtime/arch/riscv64/start.S` to allocate a minimal boot stack, call `main`, and spin afterward.
- Updated `snippets/scalar_load_legality/unaligned_load.c` so the `__riscv` path uses inline assembly with `lw` while preserving the host-side fallback used by local x86 compilation tests.
- Updated `generator/xsgen/suite_loader.py` to reject boolean, floating-point, and negative seeds with a clear `invalid seed` error.

## Unresolved Issues
- No blocking issues remain from this review finding.
- A fresh Codex review is still needed to close the review loop on the updated post-fix state.
- Queued only: the `compose.ops` vs `compose.snippets` documentation mismatch and the same-suite concurrent build race.

## Validation
- Ran `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_emitter_propagates_non_default_suite_seed` and confirmed the new regression passes after the emitter fix.
- Ran `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_manifest_loader_rejects_unsupported_lang tests.test_snippet_loading.SnippetLoadingTest.test_declared_python_dependency` and confirmed both regressions pass.
- Ran `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_duplicate_snippet_reference_builds_once_per_source` and confirmed repeated snippet references now build cleanly.
- Ran `python3 -m unittest tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_headers_expose_minimal_api tests.test_snippet_loading.SnippetLoadingTest.test_suite_loader_rejects_non_integer_or_negative_seed tests.test_snippet_loading.SnippetLoadingTest.test_unaligned_load_riscv_path_uses_real_word_load` and confirmed the three review regressions pass.
- Ran `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline` and confirmed `Ran 28 tests ... OK`.
- Ran `python3 generator/cli.py build` and `make build` serially and confirmed both succeed on the post-fix tree.

## Goal Tracker
- Updated `goal-tracker.md` to record the Round 5 review findings, the completed fixes, the unchanged queued items, and the refreshed verification state.

## BitLesson Delta
Action: none
Lesson ID(s): NONE
Notes: `bitlesson-selector` did not surface any usable project-specific lesson for this tightly scoped review-fix round.
