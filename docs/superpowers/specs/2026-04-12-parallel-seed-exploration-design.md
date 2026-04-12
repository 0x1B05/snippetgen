# Parallel Seed Exploration Design

## Goal

Add a first-pass parallel seed exploration mode for `snippetgen run` that can execute multiple XiangShan `emu` processes concurrently while preserving the existing batch contract:

- default behavior remains serial
- only the `run` phase becomes parallel
- per-seed artifacts remain isolated
- batch ledger remains the authoritative aggregate result

## Assumptions

These assumptions are fixed for the first implementation and are not reopened in this design:

- CLI adds `--jobs <N>` with default `1`
- `emit/build` stays serial
- only `run` is parallelized
- a failing or timed out seed does not abort the batch
- the final ledger remains required
- the ledger entry order matches the input seed order, not completion order

## Current Context

The current run pipeline is implemented in [`generator/xsgen/run_batch.py`](../../../generator/xsgen/run_batch.py):

- seed selection is normalized before batch execution
- each seed is processed serially in one loop
- each iteration performs `emit -> build -> run`
- batch success/failure is derived from the final ledger by [`generator/cli.py`](../../../generator/cli.py)

The XiangShan adapter in [`targets/xiangshan-verilator/run_target.py`](../../../targets/xiangshan-verilator/run_target.py) already has the right granularity for concurrency:

- it accepts one fully prepared `RunSeedArtifacts`
- it launches one `emu` subprocess
- it writes per-seed `stdout.log`, `stderr.log`, and optional wave output

This means the correct concurrency boundary is above the target adapter, not inside it.

## Approaches Considered

### Approach 1: Fixed worker pool for run stage only

- serially prepare all per-seed artifacts
- enqueue only the `run_target()` calls onto a fixed-size worker pool
- collect results in memory
- write per-seed `run_meta.json` after each future resolves
- write the final batch ledger once all futures finish

Pros:

- smallest semantic change
- avoids concurrent build/toolchain races
- preserves current target adapter contract
- easiest to test deterministically

Cons:

- build time remains serial
- batch start-up latency is unchanged

### Approach 2: Explicit two-stage pipeline with a prepared-run queue

- stage 1 emits/builds all seeds serially into a queue of runnable artifacts
- stage 2 schedules runnable artifacts onto workers
- introduces a more explicit internal state machine for prepared vs completed seeds

Pros:

- cleaner long-term extension point
- easier to add retries or prioritization later

Cons:

- more internal structure than the first feature needs
- more refactoring than required for a minimal release

### Approach 3: Unified scheduler for build and run

- treat each seed as a task that flows through build and run within one scheduler
- allow future mixed build/run parallelism and richer resource controls

Pros:

- most extensible architecture

Cons:

- over-scoped for the requested feature
- highest correctness risk
- entangles build isolation and run isolation in one change

## Recommendation

Use Approach 1.

It matches the requested feature exactly: "parallel execute multiple emu". It changes only the run-stage scheduling policy while keeping the rest of the batch contract stable. It also gives a clean baseline for future performance work without forcing build-system changes into this release.

## Proposed Design

## CLI Contract

Extend `snippetgen run` with:

```bash
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seeds 1,2,3,4 --jobs 4
```

Rules:

- `--jobs` is optional
- default is `1`
- `--jobs` must be a positive integer
- `--jobs 1` must preserve current serial behavior
- `--jobs > len(seed_values)` is allowed; effective parallelism is capped by the number of runnable seeds

## Execution Model

The batch is split into two phases.

### Phase 1: Serial preparation

For each seed in input order:

- clone the suite with the seed override
- build the compose plan
- compute seed-specific artifact paths
- emit harness
- build ELF/bin/disasm
- create `RunSeedArtifacts`
- initialize empty `stdout.log` and `stderr.log`

If preparation fails for a seed:

- record an `error` result for that seed immediately
- write its `run_meta.json`
- do not enqueue it into the run worker pool

This preserves the current "build failures do not abort the batch" behavior.

### Phase 2: Parallel run execution

For seeds whose preparation succeeded:

- submit one run task per seed into a `ThreadPoolExecutor`
- each task performs exactly one `target_runner(artifacts=..., timeout_s=...)`
- each task returns a completed `RunEntry`

The main thread is responsible for:

- collecting completed futures
- mapping each result back to its seed
- writing per-seed `run_meta.json`
- assembling final ledger entries in the original seed order

Workers do not write the batch ledger.

## Correctness Constraints

The implementation must preserve these invariants:

- each seed writes only inside its own `seed_<N>/` directory
- no two workers share a writable file path
- the batch ledger is written once, by the main thread
- ledger entry order equals the input seed order
- every seed still gets a `run_meta.json`, even if build or run fails
- `--jobs 1` remains behaviorally equivalent to the current implementation
- the target adapter API remains single-seed and unaware of concurrency

## Data and API Changes

Minimal API extension:

- `generator/cli.py`
  - add `--jobs`
  - pass `jobs` into `run_suite_batch`

- `generator/xsgen/run_batch.py`
  - add `jobs: int = 1`
  - add validation for positive job count
  - split "prepare one seed" from "run one prepared seed"
  - use a thread pool for run scheduling

No change is required to:

- `generator/xsgen/run_target.py`
- `targets/xiangshan-verilator/run_target.py`
- ledger schema, unless a small optional field such as `jobs` is later judged useful

## Why Threads Are Acceptable Here

The parallelized work is subprocess-bound, not Python CPU-bound.

Each worker:

- launches `emu`
- waits for process completion
- reads per-seed logs

This means `ThreadPoolExecutor` is sufficient and simpler than `ProcessPoolExecutor`:

- no need to pickle plans or path-rich dataclasses across processes
- simpler exception collection
- lower implementation cost

## Failure Semantics

Per-seed failures are isolated:

- build failure: seed is marked `error`, no run task submitted
- run exception: seed is marked `error`
- target timeout: target adapter returns `timeout`
- nonzero exit: target adapter classification remains unchanged

Batch failure semantics remain unchanged:

- final command exits non-zero if any ledger entry is not `status == "ran"`

## Testing Strategy

The first implementation needs deterministic unit coverage for:

- `--jobs` parsing and validation
- `--jobs 1` preserving current behavior
- worker-pool execution over multiple seeds
- stable ledger ordering despite out-of-order completion
- per-seed `run_meta.json` creation under parallel completion
- continued execution after one seed fails

The most important concurrency test is:

- submit two or more fake run tasks
- intentionally make them finish out of order
- assert the final ledger preserves input seed order

## Risks

### Shared-state leakage

If worker code mutates shared structures directly, ordering and data integrity will become nondeterministic.

Mitigation:

- workers return immutable results
- main thread owns result aggregation and ledger writing

### Hidden build/runtime coupling

If preparation and run are not cleanly separated, later refactors may accidentally parallelize build.

Mitigation:

- introduce explicit helpers for "prepare seed" and "run prepared seed"

### Log file races

If two seeds accidentally share artifact paths, logs will corrupt each other.

Mitigation:

- preserve `artifact_paths_for_run_seed()` as the only source of per-seed directories
- add tests that assert seed-isolated outputs still exist under parallel execution

## Non-Goals

This design does not include:

- automatic job sizing
- CPU or memory auto-detection
- build-stage parallelism
- cancellation of sibling runs on first failure
- streaming aggregate console progress UI
- retries or speculative reruns

## Acceptance Criteria

- `snippetgen run ... --jobs N` is accepted for positive integers and rejected otherwise
- `--jobs 1` behaves like the current serial implementation
- multiple seeds can run concurrently in the run phase
- failures in one seed do not stop the rest of the batch
- the final ledger remains present and ordered by input seed
- existing serial run tests continue to pass
