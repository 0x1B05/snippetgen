# SnippetGen Demo

ELF-first baremetal snippet generator workspace for XiangShan-oriented workload construction, build, and run.

This repository is now beyond the initial skeleton stage. It can:

- load snippet manifests and suite YAMLs
- generate a deterministic harness
- build `test.elf`, `test.bin`, and `disasm`
- run workloads on XiangShan `emu`
- record structured run results under `build/<suite>/runs/`
- keep path-oriented and bug-hunting suites side by side

## Quick Start

### 1. Build one suite

```bash
python3 generator/cli.py build suites/scalar_load_legality_poc.yaml
```

Artifacts are written to:

- `build/scalar_load_legality_poc/test.elf`
- `build/scalar_load_legality_poc/test.bin`
- `build/scalar_load_legality_poc/disasm`
- `build/scalar_load_legality_poc/build_manifest.json`

### 2. Run one suite on XiangShan `emu`

```bash
source /home/dfpmts/XS/xs-env/env.sh
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed 4660
```

Run artifacts are written to:

- `build/<suite>/runs/run_ledger.json`
- `build/<suite>/runs/seed_<N>/test.elf`
- `build/<suite>/runs/seed_<N>/test.bin`
- `build/<suite>/runs/seed_<N>/disasm`
- `build/<suite>/runs/seed_<N>/stdout.log`
- `build/<suite>/runs/seed_<N>/stderr.log`
- `build/<suite>/runs/seed_<N>/run_meta.json`

## Repository Map

### Core directories

- `generator/`
  - CLI, suite loading, harness emission, build, run orchestration
- `runtime/`
  - baremetal runtime used by generated workloads
- `snippets/`
  - concrete workload building blocks
- `suites/`
  - ordered snippet compositions
- `targets/`
  - target-specific run adapters
- `tests/`
  - loader, build, and run pipeline regression tests
- `docs/`
  - user docs, release notes, investigations, archived plans

### Important entry files

- `generator/cli.py`
  - top-level `build`, `run`, and `dump-plan` commands
- `generator/xsgen/emitter.py`
  - emits `generated_suite.c`
- `generator/xsgen/toolchain.py`
  - compiles, links, runs `objcopy`, emits `disasm`
- `generator/xsgen/run_batch.py`
  - batch run orchestration and ledger emission
- `targets/xiangshan-verilator/run_target.py`
  - XiangShan `emu` adapter

## Stable Suites

### Build and runtime smoke suites

- `suites/scalar_load_legality_poc.yaml`
  - baseline ELF-first scalar load legality path
- `suites/vsetvl_interrupt_path_poc.yaml`
  - minimal path-oriented `vsetvl` plus interrupt-related setup
- `suites/interrupt_response_poc.yaml`
  - proves real timer interrupt delivery is visible to the runtime

### Investigation and bug-hunting suites

- `suites/vsetvl_interrupt_search_poc.yaml`
  - one-shot timer plus dense `vsetvl zero, zero, zero` search workload
- `suites/misaligned_split_store_search_poc.yaml`
  - misaligned split-store forwarding search workload for the `sqNeedDeq` bug class

## Repro Commands

### Real interrupt response

```bash
source /home/dfpmts/XS/xs-env/env.sh
python3 generator/cli.py run suites/interrupt_response_poc.yaml --seed 4660
```

Expected result:

- `run_ledger.json` records `status: "ran"`
- `stdout.log` reaches `HIT GOOD TRAP`
- the check snippet confirms that a real timer interrupt was observed

### Path-oriented `vsetvl`

```bash
source /home/dfpmts/XS/xs-env/env.sh
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed 4660
```

Expected result:

- `status: "ran"`
- `labels` include `good_trap`

### Misaligned split-store abort on pre-fix XiangShan

This case is intended for a XiangShan tree that still contains the pre-fix `sqNeedDeq` behavior.

```bash
source /home/dfpmts/XS/xs-env/env.sh
SNIPPETGEN_RUN_MAX_CYCLES=12000 SNIPPETGEN_RUN_MAX_INSTR=12000 \
python3 generator/cli.py run suites/misaligned_split_store_search_poc.yaml --seed 0 --timeout-sec 140
```

Expected result on the pre-fix `emu`:

- `run_ledger.json` records `status: "abort"`
- `stdout.log` shows difftest mismatch on the detector loads
- if LightSSS tracing is enabled in the external XiangShan tree, `seed_0/lightsss-wave` is dumped beside the logs

## XiangShan Run Requirements

The XiangShan adapter assumes:

- `source /home/dfpmts/XS/xs-env/env.sh` has been executed
- `NOOP_HOME/build/verilator-compile/emu` is available
- `NEMU_HOME/build/riscv64-nemu-interpreter-so` is available

If you need LightSSS wave dump on abort, the external XiangShan tree must also be prepared correctly:

- the `emu` must be trace-enabled, for example with `EMU_TRACE=fst`
- the local `emu.cpp` must preserve the LightSSS abort/bad-trap wakeup and `wave_path` handling

This repository does not vendor the external XiangShan tree. That setup remains a local integration step.

## Artifact Layout

### Build-only layout

```text
build/<suite>/
  generated_suite.c
  test.elf
  test.bin
  disasm
  build_manifest.json
```

### Build-plus-run layout

```text
build/<suite>/runs/
  run_ledger.json
  seed_<N>/
    generated_suite.c
    test.elf
    test.bin
    disasm
    stdout.log
    stderr.log
    run_meta.json
    lightsss-wave        # only when external XiangShan tracing is active
```

## Documentation Index

### Start here

- [`docs/2026-04-10-xiangshan-emu-workload-howto.md`](/home/dfpmts/XS/framework/snippetgen-demo/docs/2026-04-10-xiangshan-emu-workload-howto.md)
  - practical XiangShan `emu` build/run guide
- [`docs/release-notes-2026-04-11.md`](/home/dfpmts/XS/framework/snippetgen-demo/docs/release-notes-2026-04-11.md)
  - what changed in this snapshot

### Investigation notes

- [`docs/2026-04-10-vsetvl-hang-investigation-notes.md`](/home/dfpmts/XS/framework/snippetgen-demo/docs/2026-04-10-vsetvl-hang-investigation-notes.md)
  - `vsetvl` and interrupt investigation trail

### Archived planning material

- [`docs/archive/README.md`](/home/dfpmts/XS/framework/snippetgen-demo/docs/archive/README.md)
  - archived drafts, requirements, and implementation plans

## For Agents

If you are an AI agent entering this repository cold, use this order:

1. Read `README.md`
2. Read the target suite YAML in `suites/`
3. Read the referenced snippet manifests in `snippets/manifests/`
4. Read the snippet sources under `snippets/`
5. Read `generator/cli.py`, `emitter.py`, `toolchain.py`, and `run_batch.py`
6. Read `tests/test_snippet_loading.py`, `tests/test_build_pipeline.py`, and `tests/test_run_pipeline.py`

Recommended first commands:

```bash
python3 generator/cli.py dump-plan suites/misaligned_split_store_search_poc.yaml
python3 generator/cli.py build suites/misaligned_split_store_search_poc.yaml
python3 -m unittest tests.test_snippet_loading tests.test_build_pipeline
```

Avoid assumptions about:

- external XiangShan tree state
- whether LightSSS wave dump is patched in that external tree
- whether a pre-fix or post-fix `emu` is being used
