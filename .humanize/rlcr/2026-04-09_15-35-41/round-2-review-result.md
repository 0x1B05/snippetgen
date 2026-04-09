# Round 2 Review Result

Mainline Progress Verdict: ADVANCED

Goal Alignment Summary:
`ACs: 2/4 addressed | Forgotten items: 0 | Unjustified deferrals: 3`

## Mainline Gaps

1. [high] Round 2 explicitly narrowed itself to `task4` through `task7` and pushed the rest of the first-stage PoC out of scope, which does not match the original plan. The round contract says harness emission, toolchain integration, and actual `ELF/bin/build_manifest.json` artifacts were out of scope in this round, but the detail plan defines those as required lower-bound work for first-stage completion. See `./.humanize/rlcr/2026-04-09_15-35-41/round-2-contract.md:3`, `./.humanize/rlcr/2026-04-09_15-35-41/round-2-contract.md:6`, `./detail-plan.md:33`, `./detail-plan.md:59`, `./detail-plan.md:94`, and `./detail-plan.md:101`.

2. [high] `task8`, `task9`, and `task10` are still missing in the implementation, so AC-2 and AC-4 remain unsatisfied. `generator/cli.py` only loads manifests and prints plans; `cmd_build()` unconditionally exits with `build not implemented yet`, there is still no emitter or toolchain path, and the build tree still contains only `build/.gitkeep`. See `./generator/cli.py:15`, `./generator/cli.py:26`, `./generator/cli.py:40`, `./detail-plan.md:205`, `./detail-plan.md:206`, and `./detail-plan.md:207`.

3. [high] `task11` is still incomplete. The new test suite is useful for loader coverage, but it does not exercise any of the required emitter or build-path behavior: no `generated_suite.c` ordering checks, no suite reorder regeneration check, no missing descriptor or link failure, no missing runtime include failure, no successful `test.elf` or `test.bin` production, and no `build/<suite>/` stability check. See `./tests/test_snippet_loading.py:75`, `./tests/test_snippet_loading.py:172`, `./tests/test_snippet_loading.py:199`, `./detail-plan.md:35`, `./detail-plan.md:38`, `./detail-plan.md:42`, `./detail-plan.md:61`, `./detail-plan.md:69`, and `./detail-plan.md:208`.

4. [medium] The implemented rejection surface for unsupported `compose.mode` and unsupported `kind` does not match the plan. The detail plan requires unsupported compose modes to be rejected as `future-only`, and `kind: stream` to be rejected with `not implemented in ELF-first PoC`. The current code raises only generic `unsupported compose mode` and `unsupported snippet kind` errors, and the tests merely assert that `ValueError` happens, so the specified contract is not enforced. See `./generator/xsgen/suite_loader.py:25`, `./generator/xsgen/suite_loader.py:27`, `./generator/xsgen/snippet_db.py:33`, `./generator/xsgen/snippet_db.py:38`, `./tests/test_snippet_loading.py:93`, `./tests/test_snippet_loading.py:130`, `./detail-plan.md:27`, `./detail-plan.md:31`, `./detail-plan.md:53`, and `./detail-plan.md:57`.

5. [medium] AC-1's deterministic artifact-surface requirement is still missing even in the host-side model and CLI surface. `BuildArtifact` exists only as an unused dataclass, and `dump-plan` emits only `suite`, `target`, `seed`, and `snippet_ids`; it has no deterministic artifact directory or manifest-path surface. The plan requires stable target info and artifact paths under a fixed seed. See `./generator/xsgen/model.py:33`, `./generator/cli.py:30`, `./detail-plan.md:23`, and `./detail-plan.md:67`.

## Blocking Side Issues

1. None. The current blockers are missing mainline tasks, not side-path defects.

## Queued Side Issues

1. [low] `tests/test_repo_layout.py` is still only a skeleton check and should eventually be folded into stronger contract-level coverage once the emitter and build path exist, but it is not the next-round driver. See `./tests/test_repo_layout.py:7` and `./tests/test_repo_layout.py:31`.

## Goal Alignment Check

- AC-1: Advanced, but not complete. The repo now has the planned suite file, manifests, model types, snippet DB, and deterministic sequence planning, yet the failure-message contract and deterministic artifact-path surface remain incomplete.
- AC-2: Not addressed in the repository state. There is still no `emitter.py`, no generated harness, and no proof that runtime plus snippets are compiled into one target.
- AC-3: Advanced. The five snippets and `proc`-only manifest path landed and compile under the host smoke test, but the stream rejection text still does not match the specified contract.
- AC-4: Not addressed. `make build` now fails honestly instead of false-passing, but there is still no `test.elf`, `test.bin`, or `build_manifest.json`.
- Forgotten items: None. All original tasks remain represented after the tracker correction.
- Deferred items: The round contract's decision to put harness emission, toolchain integration, and actual build artifacts out of scope was not justified because those are part of the plan's lower bound.
- Plan evolution: Fixing the misleading `make build` target was valid. Re-anchoring the round to snippets plus loading only was not a valid scope reduction.

## Required Implementation Plan

1. Finish `task6` and `task7` before adding more surface area. Update `generator/xsgen/snippet_db.py` so unsupported `kind` errors explicitly say `not implemented in ELF-first PoC`, update `generator/xsgen/suite_loader.py` so unsupported compose modes explicitly say `future-only`, and strengthen `tests/test_snippet_loading.py` to assert those exact failure messages instead of only checking for `ValueError`.

2. Implement `task8` by creating `generator/xsgen/emitter.py` and wiring it into `generator/cli.py build`. The emitter must take the ordered `ComposePlan`, create `build/<suite>/generated_suite.c`, declare each descriptor symbol, call `xsrt_run_snippet()` in suite order, call `xsrt_finish_pass()` on success, and fail loudly if it cannot emit a harness that references the runtime headers and every planned snippet descriptor.

3. Implement `task9` as a real toolchain wrapper in `generator/xsgen/toolchain.py`. It must gather runtime C and assembly sources from `runtime/`, gather snippet sources from the resolved plan, compile all objects with the configured RISC-V cross toolchain, link `build/<suite>/test.elf`, run `objcopy` to produce `build/<suite>/test.bin`, and propagate failures from compile, link, and objcopy without leaving the build in a false-green state.

4. Complete `task10` through the real build entrypoint rather than through loader-only smoke checks. `generator/cli.py build` and `Makefile build` must load `suites/scalar_load_legality_poc.yaml`, emit the harness, invoke the toolchain, and write `build/<suite>/build_manifest.json` with the suite name, seed, ordered snippet IDs, resolved source paths, artifact paths, and the compile, link, and objcopy commands used to create the artifacts.

5. Complete `task11` with contract tests that cover the actual PoC chain. Add tests for generated harness ordering, suite reorder regeneration, missing descriptor failure, missing runtime include or compile-input failure, link failure, objcopy failure, stable artifact paths under `build/<suite>/`, and successful creation plus manifest contents for `test.elf`, `test.bin`, and `build_manifest.json`. Keep the current loader tests, but treat them as a subset of the full contract rather than the whole round.

6. Execute `task12` only after the artifact-producing path exists. Review the resulting snippets, emitter output, toolchain wrapper, and `build_manifest.json`, remove any accidental future-only concepts, rerun the relevant unittests and the real `make build` path, and then update the tracker only if AC-1 through AC-4 are all backed by fresh verification evidence.

## Tracker Update Note

- I updated `./.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md` to mark `task4` and `task5` as verified in Round 2 and to move `task6` and `task7` back into active work because their rejection-surface contract is still incomplete.
