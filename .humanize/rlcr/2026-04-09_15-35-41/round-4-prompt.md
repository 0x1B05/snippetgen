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
- Write the current round contract to @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-4-contract.md

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
# Round 3 Review Result

Mainline Progress Verdict: ADVANCED

Goal Alignment Summary:
`ACs: 4/4 addressed | Forgotten items: 0 | Unjustified deferrals: 0`

## Mainline Gaps

1. [high] `generator/cli.py build` still does not satisfy the Round 3 task10 contract. The prompt required `generator/cli.py build` itself to load `suites/scalar_load_legality_poc.yaml`, but the parser makes `suite` optional and `cmd_build()` blindly evaluates `REPO_ROOT / args.suite`, so the documented no-arg form crashes with `TypeError: unsupported operand type(s) for /: 'PosixPath' and 'NoneType'`. This leaves the default build entrypoint incomplete even though `make build` works through an explicit suite path. The current tests only cover `python3 generator/cli.py build suites/scalar_load_legality_poc.yaml`, so task10/task11 are still open here. See `generator/cli.py:50-57`, `generator/cli.py:76-78`, and `tests/test_build_pipeline.py:84-115`.

2. [medium] `build_manifest.json` still omits required link-command provenance. The Round 3 prompt required the manifest to record the compile, link, and objcopy commands used to create the artifacts, but `build_artifacts()` only writes `commands.compile` and `commands.objcopy`. The tests mirror that incomplete contract and therefore do not catch it. This keeps task9/task10/task11 incomplete against the reviewed plan even though the produced ELF/bin are otherwise real. See `generator/xsgen/toolchain.py:68-139` and `tests/test_build_pipeline.py:104-115`.

## Blocking Side Issues

1. [high] Failed rebuilds leave stale success artifacts behind under `build/<suite>/`, so AC-4 is not safe yet. `build_artifacts()` reuses the existing build directory and never clears old outputs before attempting a rebuild. After a prior successful build, I reproduced both failure modes on the same suite build directory:
   - forced link failure after corrupting `generated_suite.c` -> `after_link_fail False True True`
   - forced objcopy failure via a patched bad objcopy path -> `after_objcopy_fail True True True`

   In both cases the function raised as expected, but stale `test.bin` and `build_manifest.json` from the earlier successful build remained present, which leaves the build directory looking successful after failure. That is exactly the kind of false-green artifact state AC-4 is supposed to prevent. The existing tests only assert that an exception is raised; they do not assert artifact cleanup or freshness. See `generator/xsgen/toolchain.py:65-139` and `tests/test_build_pipeline.py:129-198`.

## Queued Side Issues

1. None.

## Goal Alignment Check

- AC-1: Addressed. Loader validation now rejects unsupported kinds, unsupported targets, invalid suite names, invalid snippet IDs, and future-only compose modes, and `dump-plan` stays deterministic.
- AC-2: Addressed but not fully closed. Harness emission is automatic and suite-order-sensitive, but task11 still lacks the missing default-build-path regression coverage that the round prompt required around the real entrypoint.
- AC-3: Addressed. I did not find stray future-only generator/runtime concepts in the working implementation paths, so the remaining work is not an AC-3 architecture regression.
- AC-4: Addressed but not complete. Real artifacts are produced, but the default CLI build path is incomplete, manifest provenance is incomplete, and failed rebuilds can leave stale success artifacts behind.
- Forgotten items: None. All original tasks still exist in the tracker after correction.
- Deferred items: None are justified because the remaining work is not optional follow-up; it is still part of the original first-stage build-chain contract.
- Plan evolution: Re-anchoring Round 3 to the end-to-end build chain was valid. Claiming the build path was complete was premature because task9 through task12 still have verified gaps.

## Required Implementation Plan

1. Fix `generator/cli.py build` so the no-argument form defaults to `suites/scalar_load_legality_poc.yaml`, then add a regression test that `python3 generator/cli.py build` succeeds and lands under `build/scalar_load_legality_poc/`.
2. Update `generator/xsgen/toolchain.py` so `build_manifest.json` records full provenance for the executed build, including a distinct `commands.link` entry in addition to the compile and objcopy steps, and extend the manifest assertions to require it.
3. Rework the build failure path so a failed compile/link/objcopy attempt cannot leave stale `test.elf`, `test.bin`, or `build_manifest.json` from an earlier successful build in the suite artifact directory. Add regression tests that first create a successful build, then force link failure and objcopy failure on the same suite and assert the stale outputs are gone.
4. After those fixes, rerun `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline`, `python3 generator/cli.py build`, `python3 generator/cli.py build suites/scalar_load_legality_poc.yaml`, `make dump-plan`, and `make build`, then rerun the Codex analyze pass for task12 against the fresh post-fix state.
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

- Keep the mainline objective from @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-4-contract.md stable for this round
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
2. Write your work summary into @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-4-summary.md

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
