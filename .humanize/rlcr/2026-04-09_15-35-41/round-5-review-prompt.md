# Code Review - Round 5

## Original Implementation Plan

**IMPORTANT**: The original plan that Claude is implementing is located at:
@./detail-plan.md

You MUST read this plan file first to understand the full scope of work before conducting your review.
This plan contains the complete requirements and implementation details that Claude should be following.

Based on the original plan and @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-5-prompt.md, Claude claims to have completed the work. Please conduct a thorough critical review to verify this.

---
Below is Claude's summary of the work completed:
<!-- CLAUDE's WORK SUMMARY START -->
# Round 5 Summary

## Mainline Objective
- Keep the first-stage ELF-first build path faithful to the configured suite inputs and review contract by fixing the reviewed harness-seed propagation bug plus the remaining uncommitted review-path correctness gaps without widening scope beyond the accepted PoC contract.

## Blocking Issues Fixed
- Fixed the reviewed harness seed-propagation bug in `generator/xsgen/emitter.py`.
- Declared the `PyYAML` runtime dependency in `requirements.txt`.
- Rejected unsupported snippet languages during manifest loading in `generator/xsgen/snippet_db.py`.
- Deduplicated compiled snippet sources in `generator/xsgen/toolchain.py` so repeated snippet references no longer cause duplicate-definition link failures.

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

## Unresolved Issues
- No blocking issues remain from this review finding.
- A fresh Codex review is still needed to close the review loop on the updated post-fix state.
- Queued only: the `compose.ops` vs `compose.snippets` documentation mismatch and the same-suite concurrent build race.

## Validation
- Ran `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_emitter_propagates_non_default_suite_seed` and confirmed the new regression passes after the emitter fix.
- Ran `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_manifest_loader_rejects_unsupported_lang tests.test_snippet_loading.SnippetLoadingTest.test_declared_python_dependency` and confirmed both regressions pass.
- Ran `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_duplicate_snippet_reference_builds_once_per_source` and confirmed repeated snippet references now build cleanly.
- Ran `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline` and confirmed `Ran 26 tests ... OK`.
- Ran `python3 generator/cli.py build` and `make build` serially and confirmed both succeed on the post-fix tree.

## Goal Tracker
- Updated `goal-tracker.md` to record the Round 5 review finding, the completed fix, the unchanged queued items, and the refreshed verification state.

## BitLesson Delta
Action: none
Lesson ID(s): NONE
Notes: `bitlesson-selector` did not surface any usable project-specific lesson for this tightly scoped review-fix round.
<!-- CLAUDE's WORK SUMMARY  END  -->
---

## Part 1: Implementation Review

- Your task is to conduct a deep critical review, focusing on finding implementation issues and identifying gaps between "plan-design" and actual implementation.
- Relevant top-level guidance documents, phased implementation plans, and other important documentation and implementation references are located under @docs.
- If Claude planned to defer any tasks to future phases in its summary, DO NOT follow its lead. Instead, you should force Claude to complete ALL tasks as planned.
  - Such deferred tasks are considered incomplete work and should be flagged in your review comments, requiring Claude to address them.
  - If Claude planned to defer any tasks, please explore the codebase in-depth and draft a detailed implementation plan. This plan should be included in your review comments for Claude to follow.
  - Your review should be meticulous and skeptical. Look for any discrepancies, missing features, incomplete implementations.
- If Claude does not plan to defer any tasks, but honestly admits that some tasks are still pending (not yet completed), you should also include those pending tasks in your review.
  - Your review should elaborate on those unfinished tasks, explore the codebase, and draft an implementation plan.
  - A good engineering implementation plan should be **singular, directive, and definitive**, rather than discussing multiple possible implementation options.
  - The implementation plan should be **unambiguous**, internally consistent, and coherent from beginning to end, so that **Claude can execute the work accurately and without error**.

## Part 2: Goal Alignment Check (MANDATORY)

Read @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md and verify:

1. **Acceptance Criteria Progress**: For each AC, is progress being made? Are any ACs being ignored?
2. **Forgotten Items**: Are there tasks from the original plan that are not tracked in Active/Completed/Deferred?
3. **Deferred Items**: Are deferrals justified? Do they block any ACs?
4. **Plan Evolution**: If Claude modified the plan, is the justification valid?

Include a brief Goal Alignment Summary in your review:
```
ACs: X/Y addressed | Forgotten items: N | Unjustified deferrals: N
```

## Part 3: Required Finding Classification

You MUST classify your findings into these lanes:
- **Mainline Gaps**: plan-derived work or AC progress that is missing, incomplete, or regressing
- **Blocking Side Issues**: bugs or implementation issues that block the current mainline objective from succeeding safely
- **Queued Side Issues**: valid non-blocking follow-up issues that should be documented but must NOT take over the next round

Also include a one-line verdict:
```
Mainline Progress Verdict: ADVANCED / STALLED / REGRESSED
```

This verdict line is mandatory. If you omit it, the Humanize stop hook will block the round and require the review to be rerun.

If Claude mostly worked on queued side issues and failed to advance the mainline, say so explicitly.

## Part 4: ## Goal Tracker Update Requests (YOUR RESPONSIBILITY)

Claude should normally keep the **mutable section** of `goal-tracker.md` up to date directly. If Claude's summary contains a "Goal Tracker Update Request" section, or if you detect tracker drift during review, YOU must:

1. **Evaluate the tracker state**: Is the mutable section still aligned with the Ultimate Goal and current AC progress?
2. **If correction is needed**: Update @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/goal-tracker.md yourself with the requested changes:
   - Move tasks between Active/Completed/Deferred sections as appropriate
   - Add entries to "Plan Evolution Log" with round number and justification
   - Add new issues to "Blocking Side Issues" or "Queued Side Issues" as appropriate
   - **NEVER modify the IMMUTABLE SECTION** (Ultimate Goal and Acceptance Criteria)
3. **If you reject a requested tracker change**: Include in your review why it was rejected

Common update requests you should handle:
- Task completion: Move from "Active Tasks" to "Completed and Verified"
- New blocking issues: Add to "Blocking Side Issues"
- New queued issues: Add to "Queued Side Issues"
- Plan changes: Add to "Plan Evolution Log" with your assessment
- Deferrals: Only allow with strong justification; add to "Explicitly Deferred"

## Part 5: Output Requirements

- In short, your review comments can include: problems/findings/blockers; claims that don't match reality; implementation plans for deferred work (to be implemented now); implementation plans for unfinished work; goal alignment issues.
- Your output should be structured so Claude can tell which items are mainline gaps, blocking side issues, and queued side issues.
- If after your investigation the actual situation does not match what Claude claims to have completed, or there is pending work to be done, output your review comments to @/home/dfpmts/XS/framework/snippetgen-demo/.humanize/rlcr/2026-04-09_15-35-41/round-5-review-result.md.
- **CRITICAL**: Only output "COMPLETE" as the last line if ALL tasks from the original plan are FULLY completed with no deferrals
  - DEFERRED items are considered INCOMPLETE - do NOT output COMPLETE if any task is deferred
  - UNFINISHED items are considered INCOMPLETE - do NOT output COMPLETE if any task is pending
  - The ONLY condition for COMPLETE is: all original plan tasks are done, all ACs are met, no deferrals or pending work allowed
- The word COMPLETE on the last line will stop Claude.
