Your work is not finished. Read and execute the below with ultrathink.

## Original Implementation Plan

**IMPORTANT**: Before proceeding, review the original plan you are implementing:
@./detail-plan.md

This plan contains the full scope of work and requirements. Ensure your work aligns with this plan.

---

## Round Re-anchor (REQUIRED FIRST STEP)

Before writing code:
- Re-read @./detail-plan.md
- Re-read @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md
- Re-read the most recent round summaries/reviews that led to this round
- Write the current round contract to @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-2-contract.md

Your round contract must contain:
- Exactly one **mainline objective**
- The 1-2 target ACs for this round
- Which issues are truly **blocking** that mainline objective
- Which issues are **queued** and explicitly out of scope
- Concrete success criteria for this round

Do not start implementation until the round contract exists.

## Task Lane Rules

Use the Task system (TaskCreate, TaskUpdate, TaskList) with one required tag per task:
- `[mainline]` for plan-derived work that directly advances this round's objective
- `[blocking]` for issues that prevent the mainline objective from succeeding safely
- `[queued]` for non-blocking bugs, cleanup, or follow-up work

Rules:
- `[mainline]` work is the round's primary success condition
- `[blocking]` work is allowed only when it truly blocks the mainline objective
- `[queued]` work must be documented but must NOT replace the round objective
- If a new bug does not block the current objective, tag it `[queued]` and keep moving on mainline work

Before executing each task in this round:
1. Read @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/bitlesson.md
2. Run `bitlesson-selector` for each task/sub-task
3. Follow selected lesson IDs (or `NONE`) during implementation

---
Below is Codex's review result:
<!-- CODEX's REVIEW RESULT START -->
# Round 1 Review Result

Mainline Progress Verdict: ADVANCED

Goal Alignment Summary:
`ACs: 2/4 addressed | Forgotten items: 0 | Unjustified deferrals: 9`

## Mainline Gaps

1. [high] `task2` and `task3` are now verifiable, but the repository still lacks every downstream deliverable that makes the ELF-first PoC complete: the five snippets and manifests, the generator model/loader/emitter/toolchain modules, the PoC suite YAML, the contract tests for loader and emitter failure modes, and the actual `ELF/bin` artifacts. The plan defines these as `task4` through `task12`, and the first-stage lower bound explicitly says the phase is incomplete if any of `suite.yaml` parsing, snippet resolution, harness generation, `test.elf`, or `test.bin` is missing. See `detail-plan.md:94-101` and `detail-plan.md:196-209`. The current tree still has no `generator/cli.py`, `generator/xsgen/model.py`, `generator/xsgen/snippet_db.py`, `generator/xsgen/suite_loader.py`, `generator/xsgen/emitter.py`, `generator/xsgen/toolchain.py`, `suites/scalar_load_legality_poc.yaml`, or any snippet `.c` and manifest `.yaml` files under `snippets/core/`, `snippets/scalar_load_legality/`, and `snippets/manifests/`.

2. [high] Round 1’s contract improperly moved the plan’s remaining mainline into the queued lane. `round-1-contract.md` explicitly marks host-side generator modules, suite YAML, snippet manifests, and end-to-end `ELF/bin` build work as “out of scope,” even though those items are the plan’s required lower bound and directly map to `task4` through `task12`. See `.humanize/rlcr/2026-04-09_15-35-41/round-1-contract.md:3-7` and `detail-plan.md:94-101`. The runtime and ABI work is real progress, but queueing the rest is an unjustified deferral that leaves AC-1, AC-2, and AC-4 largely untouched.

3. [medium] The required contract tests for the actual PoC behavior are still absent. `tests/test_runtime_surface.py` only checks file existence, header text snippets, and a host-compiled smoke binary; it does not cover the negative and deterministic cases mandated by the plan: missing manifest fields, nonexistent snippet IDs, unsupported `compose.mode`, unsupported `kind: stream`, generated harness ordering, missing descriptor or link failures, or artifact path stability. See `tests/test_runtime_surface.py:10-191` and `detail-plan.md:20-71`, `detail-plan.md:208`. Until `task11` is implemented, the repository has no automated guardrail for most of AC-1, AC-2, AC-3.1, or AC-4.

## Blocking Side Issues

1. [medium] `make build` is currently a false-positive no-op. `Makefile` only defines `test-layout`, but because the repository already contains a `build/` directory, GNU Make treats `build` as an up-to-date target and exits successfully without generating anything. I reproduced this locally: `make build` returned success, while `find build -maxdepth 3 -type f` still showed only `build/.gitkeep`. See `Makefile:1-4`. This blocks safe AC-4 verification because the top-level build entrypoint can appear green before any generator or toolchain path exists.

## Queued Side Issues

1. [low] `tests/test_repo_layout.py` remains a very weak skeleton check. It asserts only `Makefile`, `README.md`, and directory existence, so it still cannot prove the task1 bootstrap surface described in the execution-prep doc. See `tests/test_repo_layout.py:7-40` and `/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md:62-99`. This should be folded into the stronger task11 test pass instead of becoming a separate round objective.

2. [low] The RISC-V entry stubs are still placeholders that immediately `ret`, so there is no meaningful target-side boot or trap path yet. See `runtime/arch/riscv64/start.S:1-4` and `runtime/arch/riscv64/trap.S:1-4`. That is not the current gating problem because the generator and build chain are still missing, but these stubs will need to be replaced once the toolchain is emitting a real bare-metal ELF.

## Required Implementation Plan

1. Implement `task4` completely. Add the five PoC snippets and their manifests at the planned paths: `snippets/core/init_basic_env.c`, `snippets/core/finish_check.c`, `snippets/scalar_load_legality/arm_timer.c`, `snippets/scalar_load_legality/unaligned_load.c`, `snippets/scalar_load_legality/check_scalar_load_legality.c`, plus the matching manifest YAML files under `snippets/manifests/`. Each snippet must export a descriptor symbol using the shared `xsrt_snippet_desc_t` ABI, and each manifest must provide at least `id`, `kind`, `lang`, and `sources`. Restrict V1 to `kind: proc`.

2. Implement the host-side model and loading layer for `task5`, `task6`, and `task7`. Create `generator/cli.py`, `generator/xsgen/model.py`, `generator/xsgen/snippet_db.py`, and `generator/xsgen/suite_loader.py`. The models must represent `SnippetSpec`, `SuiteSpec`, `ComposePlan`, and `BuildArtifact`. `snippet_db.py` must scan `snippets/manifests/*.yaml`, validate required fields, reject unsupported `kind`, and resolve each source path relative to the repository root. `suite_loader.py` must load `suites/scalar_load_legality_poc.yaml`, accept only `compose.mode: sequence`, reject future-only modes explicitly, and produce a deterministic ordered plan from the fixed suite seed.

3. Implement `task8` by adding `generator/xsgen/emitter.py` and wiring it from the CLI. The emitter must generate `build/<suite>/generated_suite.c` from the resolved ordered plan, declare each descriptor symbol, call `xsrt_run_snippet()` in suite order, and finish with `xsrt_finish_pass()`. Do not check in a static harness as a substitute; the generated file must change when suite order changes.

4. Implement `task9` and `task10` as a single end-to-end build path. Add `generator/xsgen/toolchain.py` plus the PoC suite file `suites/scalar_load_legality_poc.yaml`. The toolchain wrapper must compile runtime C and S sources, snippet sources, and the generated harness with the RISC-V cross compiler, link `build/<suite>/test.elf`, run `objcopy` to create `build/<suite>/test.bin`, and write `build/<suite>/build_manifest.json` containing the suite name, seed, ordered snippet IDs, resolved source paths, and the compile or link commands. Then add an explicit top-level `build` target and `generator/cli.py build` entrypoint that fail if any expected artifact is missing.

5. Implement `task11` with real positive and negative tests. Add tests that cover manifest field validation, nonexistent snippet IDs, unsupported `compose.mode`, unsupported `kind: stream`, deterministic plan output under a fixed seed, harness emission ordering, missing descriptor or link failure, and artifact path stability under `build/<suite>/`. Keep `tests/test_repo_layout.py` only as a smoke check after the contract tests exist.

6. After the artifacts and tests exist, execute `task12` as the required analyze pass. Review the produced snippets, manifests, generator modules, and build manifest, then prune any future-only concepts such as mixing, probe catalogs, or adaptive loops before claiming alignment with AC-3 and AC-4.

## Goal Alignment Check

- AC-1: Not meaningfully addressed in the repository state. There is still no suite YAML, no manifest database, and no deterministic planning path.
- AC-2: Partially advanced by the snippet ABI and helper runner, but the actual harness generator and descriptor integration path do not exist yet.
- AC-3: Advanced by the runtime surface and snippet ABI stubs, but not complete because the five planned `proc` snippets and manifest-side `kind` enforcement are still missing.
- AC-4: Not addressed. There is no generator or toolchain path, no `test.elf`, no `test.bin`, no `build_manifest.json`, and the current `make build` behavior is misleadingly green because it is a directory no-op.
- Forgotten items: None in the tracker. All original tasks remain accounted for after verifying `task2` and `task3`.
- Deferred items: The round contract’s “Queued Side Issues Out of Scope” line is not justified because it defers the plan’s lower-bound mainline work and blocks AC-1, AC-2, and AC-4.
- Plan evolution: Verifying `task2` and `task3` first is reasonable sequencing. Treating `task4` through `task12` as out of scope for the round is not a valid plan evolution and should not be carried forward.

## Tracker Note

- I updated `.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md` to mark `task2` and `task3` as verified in Round 1.
- I added the false-positive `make build` behavior to the tracker’s blocking issues so the next round cannot claim AC-4 progress without a real build entrypoint.
<!-- CODEX's REVIEW RESULT  END  -->
---

## Goal Tracker Reference

Before starting work, **read** @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md to understand:
- The Ultimate Goal and Acceptance Criteria you're working toward
- Which tasks are Active, Completed, or Deferred
- Which side issues are blocking vs queued
- Any Plan Evolution that has occurred
- The latest side-issue state that needs attention

**IMPORTANT**: Keep the mutable section of `goal-tracker.md` up to date during the round.
Do NOT change the immutable section after Round 0.
If you cannot safely reconcile the tracker yourself, include an optional "Goal Tracker Update Request" section in your summary (see below).

## Mainline Guardrails

- Keep the mainline objective from @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-2-contract.md stable for this round
- Do not let queued issues take over the round
- If Codex reported several findings, classify them into:
  - mainline gaps
  - blocking side issues
  - queued side issues
- Only mainline gaps and blocking side issues should drive the next code changes

---

Note: You MUST NOT try to exit by lying, editing loop state files, or executing `cancel-rlcr-loop`.

After completing the work, please:
0. If the `code-simplifier` plugin is installed, use it to review and optimize your code. Invoke via: `/code-simplifier`, `@agent-code-simplifier`, or `@code-simplifier:code-simplifier (agent)`
1. Commit your changes with a descriptive commit message
2. Write your work summary into @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-2-summary.md

## Task Tag Routing Reminder

Follow the plan's per-task routing tags strictly:
- `coding` task -> Claude executes directly
- `analyze` task -> execute via `/humanize:ask-codex`, then integrate the result
- Keep Goal Tracker Active Tasks columns `Tag` and `Owner` aligned with execution

**Optional fallback**: if you could not safely update the mutable section of `goal-tracker.md` directly, include this section in your summary:
```markdown
## Goal Tracker Update Request

### Requested Changes:
- [E.g., "Mark Task X as completed with evidence: tests pass"]
- [E.g., "Add to Blocking Side Issues: bug Y blocks AC-2"]
- [E.g., "Add to Queued Side Issues: cleanup Z is non-blocking"]
- [E.g., "Plan Evolution: changed approach from A to B because..."]
- [E.g., "Defer Task Z because... (impact on AC: none/minimal)"]

### Justification:
[Explain why these changes are needed and how they serve the Ultimate Goal]
```

Codex will review your request and reconcile the Goal Tracker if justified.
