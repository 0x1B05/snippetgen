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
- Write the current round contract to @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-1-contract.md

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
# Round 0 Review Result

Mainline Progress Verdict: ADVANCED

Goal Alignment Summary:
`ACs: 1/4 addressed | Forgotten items: 0 | Unjustified deferrals: 11`

## Mainline Gaps

1. [high] The round stopped after `task1`, but the original plan’s PoC is defined by `task2` through `task12`: runtime API, snippet ABI, five snippets plus manifests, generator models/loaders/emitter/toolchain, the suite YAML, end-to-end `ELF/bin` generation, negative tests, and the final analyze pass are all still missing. This is not a small follow-up; it is the bulk of the implementation required by the plan. See `detail-plan.md:198-209`, `detail-plan.md:94-101`, and `.humanize/rlcr/2026-04-09_15-35-41/round-0-contract.md:3-7`. The checked-in tree currently contains only `Makefile`, `README.md`, `generator/xsgen/__init__.py`, the layout test, and empty placeholder directories, so AC-1/AC-2/AC-3 are untouched and AC-4 is only scaffolded, not satisfied.

2. [high] The summary’s “Remaining Items” section is an effective deferral of the entire PoC despite the plan’s explicit lower bound requiring suite parsing, snippet resolution, harness generation, `test.elf`, and `test.bin` before the first stage can be considered complete. See `detail-plan.md:94-101` and `.humanize/rlcr/2026-04-09_15-35-41/round-0-summary.md`. Treating the rest as “next round” work is not justified for a completion claim; the current repository is still pre-implementation for the actual ELF-first chain.

## Blocking Side Issues

1. [medium] The verification is too weak to prove even the bootstrap skeleton is aligned with the referenced execution-prep design. The prep doc’s minimal tree includes concrete bootstrap files such as `generator/cli.py`, `generator/xsgen/model.py`, `generator/xsgen/snippet_db.py`, `generator/xsgen/suite_loader.py`, `generator/xsgen/emitter.py`, `generator/xsgen/toolchain.py`, runtime headers/sources, snippet manifests, and `suites/scalar_load_legality_poc.yaml`, but `tests/test_repo_layout.py` only checks two top-level files and directory existence. See `/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md:75-129`, `tests/test_repo_layout.py:7-40`, and `Makefile:1-4`. As written, `make test-layout` can pass while most of the expected bootstrap files are absent.

## Queued Side Issues

1. [low] The README/Makefile skeleton is under-specified relative to the broader design docs. `README.md` does not yet provide the task-1 documentation sections (`Purpose`, `Scope`, `Directory Layout`, `Current Demo Limitations`) and `Makefile` does not expose the placeholder `build`, `run`, `list-snippets`, and `clean` targets called for in the broader draft. See `README.md:1-16`, `Makefile:1-4`, and `/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-scalar-load-legality-demo-plan-draft.md:158-169`. This does not block the core PoC, but it should be cleaned up while finishing the remaining mainline work.

## Required Implementation Plan

1. Implement the minimal runtime baseline in `runtime/include/`, `runtime/src/`, `runtime/arch/riscv64/`, and `runtime/platform/xiangshan/` using the exact API frozen in `detail-plan.md:137-176` and `/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md:133-177`. That work must include `xsrt_env_t`, `xsrt_init`, `xsrt_finish_pass`, `xsrt_finish_fail`, CSR read/write helpers, trap install, timer enable/arm helpers, and the minimum XiangShan-facing platform glue needed for a bare-metal link.

2. Define the snippet ABI in `snippets/include/xs_snippet.h` and add the helper runner for `init/run/check/fini` calling. Keep V1 restricted to `kind: proc`, and reject `kind: stream` explicitly during manifest loading as required by AC-3.1.

3. Implement the five PoC snippets and manifests named in `detail-plan.md:201` and `/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md:99-129`: `init_basic_env`, `arm_timer`, `unaligned_load`, `check_scalar_load_legality`, and `finish_check`. Each snippet must export its descriptor symbol and compile under the shared ABI without relying on future-only runtime concepts.

4. Build the host-side generator proper: add `generator/cli.py`, `generator/xsgen/model.py`, `generator/xsgen/snippet_db.py`, `generator/xsgen/suite_loader.py`, `generator/xsgen/emitter.py`, and `generator/xsgen/toolchain.py`. `snippet_db.py` must validate manifest required fields and resolve source paths. `suite_loader.py` must accept only `compose.mode: sequence` and deterministically produce the same plan for the same seed. `emitter.py` must generate `build/<suite>/generated_suite.c` from the ordered snippet list. `toolchain.py` must compile runtime + snippets + harness, link `test.elf`, run `objcopy` to `test.bin`, and emit `build_manifest.json`.

5. Add `suites/scalar_load_legality_poc.yaml` and wire the top-level build entrypoint so one command exercises the full path from suite/manifest loading to `build/scalar_load_legality_poc/test.elf`, `build/scalar_load_legality_poc/test.bin`, and `build/scalar_load_legality_poc/build_manifest.json`.

6. Replace the current layout-only guardrail with substantive tests for the actual first-stage contract: missing manifest fields, nonexistent snippet IDs, unsupported `compose.mode`, unsupported `kind`, deterministic plan ordering, harness emission ordering, missing descriptor/link failures, and artifact path stability. The current `tests/test_repo_layout.py` can remain only as a smoke check after it is extended to assert the concrete bootstrap files that task1 is supposed to establish.

7. After the end-to-end build exists, execute `task12` as the required Codex analyze pass and prune any accidental future-only dependencies such as mixing, probe catalogs, or adaptive-loop concepts before claiming alignment with AC-3/AC-4.

## Goal Alignment Check

- AC-1: Not yet meaningfully addressed. There is no suite YAML, no manifest database, no suite loader, and no deterministic plan output.
- AC-2: Not addressed. There is no snippet ABI, no emitter, and no generated harness.
- AC-3: Not addressed. No runtime headers/sources or snippet descriptors exist yet.
- AC-4: Partially addressed only at the scaffolding level. The repository has a `build/` directory and a `make test-layout` target, but there is still no toolchain wrapper and no `test.elf`, `test.bin`, or `build_manifest.json`.
- Forgotten items: None in the tracker. `task2` through `task12` are still listed.
- Deferred items: The round contract and summary defer the substantive work without a technical blocker. That deferral blocks AC-1 through AC-4 from being satisfied.
- Plan evolution: Normalizing the immutable goal/ACs in the tracker is fine. Narrowing the round to `task1` is acceptable only as sequencing, not as evidence that the plan’s functional goal is close to complete.

## Tracker Note

- I updated `.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md` to move `task1` out of `Active Tasks` and mark it verified in Round 0. I did not accept any scope reduction beyond that; `task2` through `task12` remain pending mainline work.
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

- Keep the mainline objective from @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-1-contract.md stable for this round
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
2. Write your work summary into @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-1-summary.md

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
