# Round 3 Summary

## Work Completed
- Re-anchored Round 3 to the remaining first-stage build chain and wrote `round-3-contract.md` with one mainline objective: finish the rejection contracts, emitter, toolchain, and real build path.
- Tightened the loader-layer contract:
  - unsupported snippet kinds now fail with `not implemented in ELF-first PoC`
  - unsupported compose modes now fail with `future-only`
  - unsupported targets are rejected
  - invalid snippet IDs and invalid suite names are rejected before they can leak into symbol generation or artifact paths
- Implemented `generator/xsgen/emitter.py` to emit `build/<suite>/generated_suite.c` from the ordered plan and call `xsrt_run_snippet()` in suite order.
- Implemented `generator/xsgen/toolchain.py` to:
  - discover the RISC-V cross toolchain
  - compute stable artifact paths under `build/<suite>/`
  - compile runtime, snippet sources, and generated harness into `test.elf`
  - run `objcopy` to create `test.bin`
  - write `build_manifest.json` with suite metadata, source paths, artifact paths, and commands
- Updated `generator/cli.py build` to run the full load -> emit -> build flow, and updated `dump-plan` to expose the stable artifact path surface.
- Fixed a bare-metal compatibility issue in `runtime/src/xsrt_env.c` by removing the libc dependency and then restoring the needed `NULL` definition via `<stddef.h>`.
- Extended the contract tests to cover:
  - exact rejection text
  - suite reorder regeneration
  - real build success
  - artifact path stability
  - missing descriptor failure
  - missing compile input failure
  - objcopy failure
- Started the required Codex analyze pass for `task12`, used its findings to close two remaining contract seams (unsupported target acceptance and unsanitized suite/snippet identifiers), and revalidated after the fixes.

## Files Changed
- Updated `.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md`
- Created `.humanize/rlcr/2026-04-09_15-35-41/round-3-contract.md`
- Updated `.humanize/rlcr/2026-04-09_15-35-41/round-3-summary.md`
- Updated `generator/cli.py`
- Added `generator/xsgen/emitter.py`
- Added `generator/xsgen/toolchain.py`
- Updated `generator/xsgen/model.py`
- Updated `generator/xsgen/snippet_db.py`
- Updated `generator/xsgen/suite_loader.py`
- Updated `runtime/src/xsrt_env.c`
- Updated `tests/test_snippet_loading.py`
- Added `tests/test_build_pipeline.py`

## Validation
- Ran `python3 -m unittest tests/test_snippet_loading.py` after tightening the loader contract and confirmed all 10 tests passed.
- Ran `python3 -m unittest tests/test_build_pipeline.py` after adding emitter/toolchain/build coverage and confirmed all 7 tests passed.
- Ran `python3 -m unittest tests/test_runtime_surface.py` and confirmed all 3 tests still passed.
- Ran `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline` and confirmed the combined suite passed: `Ran 20 tests ... OK`.
- Ran `make list-snippets` and confirmed the five PoC snippet IDs were listed.
- Ran `make dump-plan` and confirmed the deterministic ordered plan plus stable artifact paths were emitted for `scalar_load_legality_poc`.
- Ran `make build` and confirmed it produced:
  - `build/scalar_load_legality_poc/generated_suite.c`
  - `build/scalar_load_legality_poc/test.elf`
  - `build/scalar_load_legality_poc/test.bin`
  - `build/scalar_load_legality_poc/build_manifest.json`
- Ran an ask-Codex analyze pass for `task12`; while that review was still running, its log surfaced unsupported-target acceptance and unsanitized suite/snippet identifiers, both of which were fixed and then revalidated by the test and build commands above.

## Remaining Items
- The RLCR stop-gate review for Round 3 has not been run yet, so `task6` through `task12` are complete pending Codex verification.
- The follow-up ask-Codex analyze processes are still asynchronous, so they may eventually write stale observations against the pre-fix state. The current local verification evidence reflects the post-fix state and should be treated as source of truth for this round's summary.
- If the Round 3 RLCR review finds no new issues, the next transition should be the RLCR review/finalize path rather than more feature work.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: The project-specific BitLesson file is still empty, and the selector did not surface any reusable lesson for this emitter/toolchain/build-path round.
