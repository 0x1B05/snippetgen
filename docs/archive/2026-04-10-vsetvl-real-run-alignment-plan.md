# Vsetvl Real-Run Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `snippetgen-demo` 生成的 `vsetvl_interrupt_path_poc` 镜像能在 XiangShan `emu` 的真实运行模式下进入可提交状态，并据此判断是否真的出现卡死。

**Architecture:** 先修正运行契约而不是继续追 `vsetvl` 本体。当前证据说明问题发生在 snippet 提交之前：镜像在正确 `xs-env` 环境下能启动 `emu` 和 NEMU 参考模型，但在低 cycle limit 下仍然 `instrCnt = 0`。因此本轮主线是对齐 `snippetgen-demo` 与 `nexus-am`/XiangShan 的启动、链接和运行参数契约，再用真实运行验证是否进入 snippet 路径。

**Tech Stack:** Python CLI, RISC-V baremetal runtime, XiangShan `emu`, NEMU reference model, unittest

---

## Scope

- 修正真实运行前的启动契约与运行参数
- 保留 `vsetvl_interrupt_path_poc` 的 path-oriented 语义，不扩展 probe/checker
- 暂不做随机化、多 seed 批跑、RTL 内部机制验证

## Current Evidence Anchor

- 已经确认 `source /home/dfpmts/XS/xs-env/env.sh` 是必须条件
- 已经确认 `main()` 返回后的死循环曾经是一个问题，并已改成发出 noop/XiangShan halt trap
- 已经确认在正确环境下，`emu` 能找到 `NEMU` 参考模型
- 已经确认在低上限实跑时得到的是：
  - `EXCEEDING CYCLE/INSTR LIMIT`
  - `instrCnt = 0`
  - 说明当前问题仍早于 snippet 执行与提交

## Task 1: Lock The Real-Run Contract

**Files:**
- Modify: `tests/test_build_pipeline.py`
- Inspect: `runtime/arch/riscv64/start.S`
- Inspect: `generator/xsgen/toolchain.py`

- [ ] **Step 1: Keep the existing `_start` halt-trap regression**

Purpose: 锁住“`main()` 返回后不能再直接自旋”的行为，防止后续启动对齐时回退。

- [ ] **Step 2: Add one more non-flaky build-side assertion for the real-run contract**

Check one of these exact properties:
- `_start` 仍然先跳 `main`
- `_start` 返回路径仍然包含 `0x0005006b`
- 最终 ELF 的 entry section 没有退回纯自旋收尾

- [ ] **Step 3: Verify the focused build test**

Run:
```bash
python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_runtime_entry_emits_noop_halt_trap_after_main_returns
```

Expected:
- PASS

## Task 2: Align Boot And Linker Contract To XiangShan/Noop

**Files:**
- Modify: `runtime/arch/riscv64/start.S`
- Create: `runtime/platform/xiangshan/section.ld`
- Modify: `generator/xsgen/toolchain.py`
- Inspect: `/home/dfpmts/XS/xs-env/nexus-am/am/src/xs/isa/riscv/boot/start_dual.S`
- Inspect: `/home/dfpmts/XS/xs-env/nexus-am/am/src/xs/ldscript/section.ld`

- [ ] **Step 1: Introduce a platform linker script instead of raw `-Ttext=0x80000000`**

The linker script should minimally define:
- `ENTRY(_start)`
- `.text`, `.rodata`, `.data`, `.bss`
- `_stack_top`
- `_heap_start`
- `_pmem_start`
- `_pmem_end`

Purpose:
- 对齐 XiangShan/noop 的镜像布局约定
- 避免当前最小链接方式和真实 `emu` 载入模型不一致

- [ ] **Step 2: Align `_start` to the XiangShan/noop boot shape**

Bring over the minimum required ideas from the reference boot path:
- initialize stack from `_stack_top`
- initialize `tp` consistently
- preserve the return-to-halt behavior after `main`

Do not add unrelated AM subsystems.

- [ ] **Step 3: Wire the linker script into build**

Replace the current hard-coded link placement with explicit script usage in `build_artifacts()`.

- [ ] **Step 4: Verify the ELF still builds**

Run:
```bash
python3 generator/cli.py build suites/vsetvl_interrupt_path_poc.yaml
```

Expected:
- build succeeds
- `build/vsetvl_interrupt_path_poc/test.elf`
- `build/vsetvl_interrupt_path_poc/test.bin`
- `build_manifest.json`

## Task 3: Align Real Run Parameters With XiangShan Environment

**Files:**
- Modify: `targets/xiangshan-verilator/run_target.py`
- Modify: `tests/test_run_pipeline.py`

- [ ] **Step 1: Stop using the fake easy path for real XiangShan runs**

Update the adapter contract so the real-run path:
- sources `/home/dfpmts/XS/xs-env/env.sh` or equivalently injects the same env vars
- uses `emu` from `$NOOP_HOME/build/verilator-compile/emu`
- does not default to `--no-diff`
- uses `$NEMU_HOME/build/riscv64-nemu-interpreter-so` as the reference model

- [ ] **Step 2: Keep this Phase 1 adapter honest**

The adapter may still report only weak labels, but it must distinguish:
- runner/env setup failure
- limit exceeded
- good trap / sim exit if reached

- [ ] **Step 3: Add regression tests for environment-driven runner construction**

Test the adapter logic without requiring a real `emu` run in unittest:
- env sourcing/derivation inputs are honored
- the generated command line includes the reference model path
- `--no-diff` is not silently forced in the real path

## Task 4: Reproduce And Classify The Real Behavior

**Files:**
- No new source file required
- Produce evidence under: `build/vsetvl_interrupt_path_poc/`

- [ ] **Step 1: Rebuild the case**

Run:
```bash
source /home/dfpmts/XS/xs-env/env.sh
python3 generator/cli.py build suites/vsetvl_interrupt_path_poc.yaml
```

- [ ] **Step 2: Run a low-limit classification pass**

Run:
```bash
source /home/dfpmts/XS/xs-env/env.sh
$NOOP_HOME/build/verilator-compile/emu -s 4660 -C 1000 -I 20 -i build/vsetvl_interrupt_path_poc/test.bin -b 0 -e 1000 --dump-commit-trace
```

Expected acceptable outcomes:
- `HIT GOOD TRAP`
- `EXIT`
- `EXCEEDING CYCLE/INSTR LIMIT` with non-zero `instrCnt`

Unacceptable outcome:
- `instrCnt = 0`

- [ ] **Step 3: If low-limit pass is acceptable, run a realistic follow-up**

Run:
```bash
source /home/dfpmts/XS/xs-env/env.sh
$NOOP_HOME/build/verilator-compile/emu -s 4660 -C 50000 -I 5000 -i build/vsetvl_interrupt_path_poc/test.bin --force-dump-result
```

Classify the result as one of:
- reaches trap and exits
- exceeds limit after making forward progress
- stalls without forward progress

## Task 5: Final Verification And Decision

**Files:**
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_run_pipeline.py`
- Optional doc update if behavior differs from current assumptions

- [ ] **Step 1: Run the full repo matrix**

Run:
```bash
python3 -m unittest tests.test_build_pipeline tests.test_runtime_surface tests.test_run_pipeline tests.test_repo_layout tests.test_snippet_loading
```

Expected:
- PASS

- [ ] **Step 2: Record the real-run conclusion**

Required final classification:
- `boot/link mismatch fixed, case now reaches real execution`
- or `still stuck before first useful commit, next step needs deeper boot/runtime alignment`
- or `case now reaches execution and exposes a likely case-specific hang`

## Success Criteria

- `snippetgen-demo` real-run path uses the correct `xs-env`/`emu`/`NEMU` contract
- generated ELF/bin no longer relies on the old post-`main` spin loop
- low-limit real run no longer fails with `instrCnt = 0`
- only after that do we interpret longer-running behavior as possible case-specific hang

## Non-Goals

- 不在这轮里证明 `vsetvl` 精确命中 interrupt window
- 不在这轮里接入 RTL probe/checker
- 不在这轮里引入随机代码生成或多 seed 批量实跑
