# SnippetGen Demo Nexus-AM Baseline Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `snippetgen-demo` so that a `nexus-am`-style single-core `main()` program can be used as one standalone snippet, while preserving the current XiangShan integration shell (`ELF/bin/disasm`, `emu + NEMU diff`, per-seed run artifacts, wave capture, structured ledgers).

**Architecture:** Treat `nexus-am` compatibility as the new runtime baseline instead of extending the current thin `xsrt` runtime into another private framework. Build a new single-core `AM-compatible runtime + platform-driver layer + program-as-snippet adapter + XiangShan integration shell`, then keep the existing `proc` snippet model only as a lower-level primitive/checker/noise lane. Use scalar misalign validation as the first end-to-end proving ground for the new structure.

**Tech Stack:** C/C++/ASM baremetal runtime, Python generator/CLI, RISC-V cross toolchain, XiangShan `emu`, NEMU diff, YAML manifests, `unittest`.

---

## 1. Scope

This plan covers:

- making a `nexus-am` style `main()` program the default high-level authoring unit
- aligning `snippetgen-demo` to `nexus-am` single-core runtime capability level
- keeping current `snippetgen-demo` XiangShan-oriented integration features
- planning the first validation theme around scalar misalign load/store

This plan does **not** cover:

- full multi-core `MPE` enablement
- recreating STING-scale random snippet generation
- migrating all existing `nexus-am` apps/tests in the first wave
- turning `snippetgen-demo` into a general cross-platform AM build system

## 2. Problem Statement

### 2.1 Current `snippetgen-demo` weaknesses from step1

The current repository is strong as a XiangShan repro shell but weak as a reusable runtime/program framework:

- `runtime/include/xsrt_env.h`
  - only exposes a tiny runtime state object
- `snippets/include/xs_snippet.h`
  - only exposes `init/run/check/fini`
- `generator/xsgen/emitter.py`
  - just emits a sequential harness that calls snippets one by one
- `runtime/src/xsrt_intr.c`
  - directly writes platform MMIO constants instead of using a device abstraction
- `runtime/platform/xiangshan/xsrt_platform.c`
  - is only a minimal finish-code stub

This means `snippetgen-demo` currently behaves more like a focused XiangShan workload harness than a real application/runtime platform.

### 2.2 Current `nexus-am` strengths from step1

`nexus-am` already provides the missing abstraction layers:

- `am/am.h`
  - `TRM`, `IOE`, `CTE`, `VME`, `MPE`
- `am/amdev.h`
  - device namespace and register payload schemas
- `am/src/noop/isa/riscv/trm.c`
  - `_heap`, `_putc`, `_halt`, `_trm_init`
- `am/src/nemu/isa/riscv/cte.c`
  - unified event/context/handler path
- `am/src/nemu/isa/riscv/vme.c`
  - page-table init, map, fault-map, hugepage-map
- `am/src/xs/common/ioe.c`
  - device access layer
- `am/src/xs/isa/riscv/clint.c`, `plic.c`, `pma.c`, `pmp.c`, `cache.c`
  - XiangShan/noop-oriented driver helpers

### 2.3 Authoring conclusion from step2

The default authoring baseline must be:

- "write a `nexus-am` style program with `main()`"

not:

- "write a private `xsrt_snippet_desc_t` function bundle"

The existing `proc` snippet model should survive only as:

- primitive lane
- checker lane
- trigger lane
- background noise lane

### 2.4 Validation conclusion from step3

For scalar misalign validation:

- `nexus-am`-style program snippets should carry baseline correctness and VM/device/fault setup
- `snippetgen-demo` should add XiangShan-specific search, repro, seed sweep, artifact retention, wave and abort/assert hunting

The first flagship validation topic should therefore be:

- scalar misalign load/store validation using `/home/dfpmts/XS/kmh-v2/docs/scalar-misalign-validation-points-2026-04-16.md`

## 3. Target End State

At the end of this roadmap, `snippetgen-demo` should behave like this:

1. A user can add a normal AM-style program with `main()` and register it as one snippet in a suite.
2. The program runs on an internal single-core runtime whose semantics are aligned with `nexus-am` `TRM/IOE/CTE/VME`.
3. The program can still be combined with lower-level `proc` snippets for init/check/noise.
4. The repository still produces:
   - `test.elf`
   - `test.bin`
   - `disasm`
   - per-seed run directories
   - `stdout.log` / `stderr.log`
   - `run_meta.json`
   - optional `lightsss-wave`
5. Misalign validation can be expressed in two lanes:
   - baseline correctness lane
   - XiangShan search/repro lane

## 4. File Structure Plan

This section locks down the intended implementation boundaries inside `snippetgen-demo`.

### 4.1 Runtime compatibility layer

- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/am.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/amdev.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/context.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/vme.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/ioe.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsam/program_snippet.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsam_trm.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsam_cte.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsam_vme.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsam_ioe.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsam_program_snippet.c`

Responsibilities:

- mirror the single-core AM runtime surface
- provide a compatibility entry layer for AM-style programs
- keep `xsrt_*`-specific details out of AM authoring

### 4.2 Platform and device layer

- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_platform.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_clint.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_plic.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_serial.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_input.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/noop/xsam_noop_perf.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_platform.h`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_clint.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_plic.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_pma.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_pmp.c`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/xsam_xs_cache.c`

Responsibilities:

- centralize XiangShan/noop hardware knowledge
- remove direct MMIO constants from workload snippets
- expose device and platform helpers through the AM-compatible layer

### 4.3 Generator and manifest layer

- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/model.py`
- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/snippet_db.py`
- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/emitter.py`
- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/toolchain.py`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/am_program_loader.py`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/program_harness.py`

Responsibilities:

- add a new snippet kind for AM-style program snippets
- preserve `proc` snippets for lower-level primitive/checker use
- compile and link AM program snippets with the new runtime

### 4.4 Program snippet sources

- Create: `/home/dfpmts/XS/framework/snippetgen-demo/snippets/programs/`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/snippets/manifests/*.yaml` entries for AM-style program snippets
- Preserve: `/home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/*`
- Preserve: `/home/dfpmts/XS/framework/snippetgen-demo/snippets/store_forward/*`

Responsibilities:

- host AM-style `main()` programs
- host legacy primitive snippets
- allow suites to combine both

### 4.5 Validation and regression layer

- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_snippet_loading.py`
- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_build_pipeline.py`
- Modify: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_run_pipeline.py`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_am_program_snippet_runtime.py`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_am_program_snippet_build.py`
- Create: `/home/dfpmts/XS/framework/snippetgen-demo/tests/test_am_program_snippet_run.py`

Responsibilities:

- ensure the new AM program lane is not a sidecar experiment
- prove build and runtime contracts stay intact
- hold the first misalign validation matrix

## 5. Milestones

### Milestone A: Single-Core AM Runtime Baseline

**Goal:** Reach `nexus-am` single-core runtime capability level inside `snippetgen-demo`.

Must include:

- `TRM`
- `CTE`
- `VME`
- `IOE`
- single-core `MPE` stubs
- platform drivers for `timer`, `serial`, `input`, `perfcnt`
- XiangShan/noop platform separation

Exit criteria:

- A minimal AM-style `main()` can print text, exit, receive timer interrupts, and build page tables through the local runtime.

### Milestone B: Program-as-Snippet Adapter

**Goal:** A `main()` program can be registered as one standalone snippet in a suite.

Must include:

- new manifest kind, separate from `proc`
- harness support for AM program snippets
- coexistence with `proc` primitive/checker snippets
- build artifacts still produced in the current repository format

Exit criteria:

- One suite can contain:
  - an AM program snippet
  - one init/check primitive snippet
  - one finish snippet

### Milestone C: XiangShan Integration Preservation

**Goal:** Preserve all current run integration affordances while changing the authoring and runtime baseline.

Must include:

- `emu` adapter compatibility
- NEMU diff compatibility
- result classification
- per-seed directories
- wave path passthrough

Exit criteria:

- New AM program snippets still produce build and run artifacts in the same repository workflow shape.

### Milestone D: Scalar Misalign Validation Pilot

**Goal:** Use the new architecture to validate scalar misalign scenarios in both baseline-correctness and XiangShan-hunting lanes.

Must include:

- baseline correctness workloads
- VME/page-fault workloads
- search/repro workloads for XiangShan-specific windows

Exit criteria:

- The scalar misalign validation points document can be mapped into executable workload categories.

## 6. Implementation Phases

### Phase 1: Runtime semantic alignment

Focus:

- move from `xsrt`-only runtime semantics to AM-compatible single-core semantics

Deliverables:

- AM-like headers under `runtime/include/xsam/`
- runtime services for `TRM/CTE/VME/IOE`
- no direct workload dependence on `mtvec/mscratch/CLINT` constants for common flows

Acceptance checks:

- `main()` can return through a standard halt path
- `_putc()` works
- timer IRQ path is not special-cased only for one snippet
- page table mapping APIs exist and are callable from workload code

### Phase 2: Program snippet model

Focus:

- add a new first-class snippet kind for AM-style programs

Deliverables:

- generator schema changes
- AM program manifest rules
- harness support for AM snippets

Acceptance checks:

- suite planning shows the new snippet kind
- build manifest records the AM program source set
- disassembly still points to the intended target function(s)

### Phase 3: Platform driver completion

Focus:

- make the runtime/device baseline complete enough for real AM-style workloads

Deliverables:

- device layer for `timer`, `serial`, `input`, `perfcnt`
- platform-level `CLINT`, `PLIC`
- stubs or declared extension slots for `video`, `storage`, `audio`, `pciconf`
- XiangShan helpers for `PMA/PMP/cache`

Acceptance checks:

- device interactions no longer require hard-coded workload-local MMIO constants
- interrupt paths use driver/runtime APIs instead of snippet-local trap tricks

### Phase 4: Misalign pilot

Focus:

- use scalar misalign as the first full-stack proving ground

Lane A: baseline correctness

- same-16B misalign
- split-template correctness
- final data / trap / architectural observables

Lane B: VME and faulting-half

- cross-page load/store
- page permissions
- fault-map / hugepage variants
- exception address ownership

Lane C: XiangShan hunt/search

- replay
- owner/lifetime bookkeeping
- forwarding windows
- `sqNeedDeq`
- redirect/flush cleanup windows

Acceptance checks:

- the validation points document is converted into a categorized matrix
- at least one case exists for each category
- the search lane retains seed-based reproducibility and XiangShan artifact capture

## 7. Misalign Mapping Plan

Use `/home/dfpmts/XS/kmh-v2/docs/scalar-misalign-validation-points-2026-04-16.md` as the pilot matrix.

### Category A: immediately suitable for AM baseline lane

- `L1`
- `L2`
- `S1`
- `S4`

Rationale:

- architecturally visible
- data/trap results are software-checkable
- do not require large search harnesses to be meaningful

### Category B: require VME/platform completion first

- `L4`
- `L8`
- `S7`
- `S9`
- `S11`
- `C1`
- `C2`

Rationale:

- depend on page tables, permissions, MMIO, uncache, PMA or fault-map semantics

### Category C: best handled by XiangShan search/repro lane

- `L3`
- `L5`
- `L6`
- `L7`
- `L9`
- `S2`
- `S3`
- `S5`
- `S6`
- `S8`
- `S10`
- `S12`
- `C3`

Rationale:

- depend on timing, replay, ownership, forwarding, commit/dequeue, redirect or rare microarchitectural windows
- benefit from seeds, per-run artifacts, abort capture and wave preservation

## 8. What To Reuse From `nexus-am`

Directly reuse conceptually and structurally:

- `TRM`, `IOE`, `CTE`, `VME` semantics from:
  - `/home/dfpmts/XS/xs-env/nexus-am/am/am.h`
- device namespace and payloads from:
  - `/home/dfpmts/XS/xs-env/nexus-am/am/amdev.h`
- noop/xs platform driver patterns from:
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/noop/isa/riscv/trm.c`
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/nemu/isa/riscv/cte.c`
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/nemu/isa/riscv/vme.c`
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/xs/common/ioe.c`
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/xs/isa/riscv/clint.c`
  - `/home/dfpmts/XS/xs-env/nexus-am/am/src/xs/isa/riscv/plic.c`

Do **not** directly clone:

- the entire `nexus-am` build system
- the entire app/test tree
- multi-core implementation details

## 9. What Must Remain Unique To `snippetgen-demo`

Preserve and continue to strengthen:

- YAML-driven suite composition
- per-seed build/run isolation
- structured run ledgers
- `disasm` as first-class artifact
- XiangShan `emu` adapter
- NEMU diff glue
- `wave_path` and abort/bad-trap artifact capture
- focused bug-hunting suites alongside baseline suites

## 10. Risks

1. **Dual-runtime drift**
   - Risk: `xsrt` and AM-compatible runtime evolve separately.
   - Response: the AM-compatible layer becomes the new baseline; `xsrt` survives only as adapter glue or legacy primitive support.

2. **Program-snippet ABI confusion**
   - Risk: users need to understand both AM program rules and old snippet rules at once.
   - Response: make AM program snippets the default; document `proc` snippets as advanced/low-level extensions.

3. **Platform coupling leakage**
   - Risk: workloads keep hard-coding MMIO addresses.
   - Response: all new workloads that depend on timer/input/interrupt/VME must use runtime/device helpers, not raw addresses.

4. **Build flow regression**
   - Risk: upgrading runtime semantics breaks current XiangShan runs.
   - Response: preserve build artifacts and adapter contract as a separate milestone with regression tests.

5. **Misalign scope explosion**
   - Risk: scalar misalign matrix is too broad to finish in one pass.
   - Response: enforce lane split:
     - baseline correctness
     - VME/fault
     - search/repro

## 11. Acceptance Summary

This plan is complete when the following statements are all true:

- a `nexus-am`-style single-core `main()` program can be treated as one standalone snippet
- the local runtime reaches `nexus-am` single-core semantic level for `TRM/IOE/CTE/VME`
- the repository still keeps its current XiangShan integration shell strengths
- scalar misalign validation can be expressed as:
  - AM baseline workloads
  - VME/fault workloads
  - XiangShan seed-based hunt/repro workloads

## 12. Execution Notes

Recommended implementation order:

1. `P0` boundary reset
2. `P1` single-core AM runtime
3. `P3` platform/device completion in parallel with `P1`
4. `P2` program-as-snippet adapter
5. `P4` build contract stabilization
6. `P5` misalign pilot
7. `P6` cleanup and reuse boundary enforcement

This ordering intentionally delays broad `nexus-am` app migration. The first success criterion is runtime capability alignment plus one first-class AM program snippet lane, not mass porting.
