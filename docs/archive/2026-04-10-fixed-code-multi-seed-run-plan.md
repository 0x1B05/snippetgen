# Fixed-Code Multi-Seed Run Plan

## Goal Description

在 `snippetgen-demo` 中落地第一阶段 `run` 闭环，使一个固定 suite 能按多个 seed 重复执行，并为每个 seed 产出独立的：

- build artifacts
- run logs
- machine-readable result ledger

本计划的目标严格限定为：

- 固定代码、多 seed 执行
- 每个 seed 重新 build 一个 ELF
- 引入最小 target run adapter
- 记录结构化 run 结果

本计划**不**要求本轮完成：

- 随机代码生成
- 同一个 ELF 注入多个 seed
- probe 提取
- 语义 checker
- 覆盖率收敛
- `/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md` 对应内部机制验证

## Acceptance Criteria

- AC-1: `run` 子命令必须支持对一个固定 suite 进行多 seed 批执行
  - Positive Tests (expected to PASS):
    - `python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed 1234` 成功解析并为单个 seed 执行 build+run。
    - `python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seeds 1,2,3` 成功展开为三个独立 seed 条目。
    - `python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed-range 0:3` 成功展开为连续 seed 列表。
  - Negative Tests (expected to FAIL):
    - 同时缺少 `--seed`、`--seeds`、`--seed-range` 时，CLI 明确失败。
    - `--seeds` 中有非法值、空值或重复值处理不当时，CLI 明确失败。
    - 非法 range 形态，例如 `3:0`、非整数、空边界时，CLI 明确失败。

- AC-2: 每个 seed 必须产出独立 artifact 和独立 run record
  - Positive Tests (expected to PASS):
    - 对于一次 batch run，存在 `build/<suite>/runs/<timestamp>/seed_<N>/` 目录。
    - 每个 seed 目录下存在独立的 `test.elf`、`test.bin`、`stdout.log`、`stderr.log`、`run_meta.json`。
    - 每个 seed 的构建结果不会覆盖其他 seed 的结果。
  - Negative Tests (expected to FAIL):
    - 若两个 seed 写入同一未区分 seed 的 artifact 目录，判定失败。
    - 若 run 失败但 seed 目录缺失最小 meta/log 信息，判定失败。

- AC-3: 系统必须生成 machine-readable run ledger，并能回答 seed 与结果的映射关系
  - Positive Tests (expected to PASS):
    - batch 运行后生成 `run_ledger.json`。
    - ledger 中至少记录：suite、target、run_batch、seed、artifact_dir、elf、bin、status、stdout_log、stderr_log、labels。
    - ledger 可区分 `built`、`ran`、`timeout`、`nonzero_exit` 等弱标签。
  - Negative Tests (expected to FAIL):
    - run 结束后只留下终端输出，没有结构化 ledger，判定失败。
    - ledger 漏掉 seed 或将结果映射到错误 artifact，判定失败。

- AC-4: 当前阶段必须明确保持“运行结果”与“语义命中”分离
  - Positive Tests (expected to PASS):
    - 第一阶段输出只使用弱标签，不宣称复现内部 bug。
    - `run_meta.json` 和 `run_ledger.json` 中不会写入“已复现文档场景”这类结论。
    - 现有 `vsetvl_interrupt_path_poc` 仍被描述为 path-oriented case。
  - Negative Tests (expected to FAIL):
    - 没有 probe/checker 仍把结果标成“interrupt 命中窗口”或“已验证 ROB 机制”，判定失败。
    - 将 Phase 2 的 checker 语义提前硬编码进 Phase 1 ledger，判定失败。

- AC-5: 引入 `run` 闭环后，不得破坏现有 build-only 路径
  - Positive Tests (expected to PASS):
    - `python3 generator/cli.py build` 继续成功。
    - `python3 generator/cli.py build suites/vsetvl_interrupt_path_poc.yaml` 继续成功。
    - 现有 loader/build tests 继续通过。
  - Negative Tests (expected to FAIL):
    - 为实现 `run` 而破坏原有 build 目录、build_manifest 或 CLI `build` 语义，判定失败。

## Path Boundaries

### Upper Bound (Maximum Acceptable Scope)

最完整但仍然可接受的第一阶段实现包括：

- 真实 `run` CLI
- 多种 seed 输入方式
- 最小 target run adapter
- `run_ledger.json`
- 每 seed 独立 artifact/log/meta 目录
- 基础弱标签
- 针对 batch run 的单元测试

这一上界**不**包含：

- 随机代码生成
- 同 ELF 多 seed 注入协议
- probe extraction
- semantic checker
- 可疑 seed 自动重跑策略
- 覆盖率收敛逻辑

### Lower Bound (Minimum Acceptable Scope)

最小可接受实现包括：

- 一个真实可用的 `generator/cli.py run`
- 支持对固定 suite 传入多个 seed
- 每个 seed 独立 build 和 run
- 结构化 ledger 输出

只要缺少其中任意一项，就不算完成本计划。

### Allowed Choices

- Can use:
  - 现有 `suite -> plan -> build_artifacts` 路径
  - 每个 seed 一个 ELF 的执行模型
  - 新增 run/ledger dataclass 或 JSON helper
  - 新增 target adapter 目录
  - 弱标签和最小 run meta
- Cannot use:
  - 在本阶段引入随机代码生成
  - 把 Phase 2 的 probe/checker 语义硬塞进 Phase 1
  - 为了省事把多个 seed 的结果写进同一个未隔离目录
  - 把“成功运行”描述成“成功覆盖内部 bug 条件”

## Feasibility Hints and Suggestions

### Recommended File Structure

建议新增或修改以下文件：

- Modify: `generator/cli.py`
  - 增加真实 `run` 子命令解析和调用路径
- Modify: `generator/xsgen/model.py`
  - 增加 run 相关 dataclass，例如 `RunArtifact`、`RunEntry`、`RunLedger`
- Modify: `generator/xsgen/toolchain.py`
  - 增加 seed-aware artifact path helper，支持把 artifacts 写到 `runs/<timestamp>/seed_<N>/`
- Create: `generator/xsgen/run_batch.py`
  - 负责 seed 展开、批处理执行、目录布局、结果聚合
- Create: `generator/xsgen/run_target.py`
  - 定义 target run adapter 的最小接口
- Create: `targets/xiangshan-verilator/run_target.py`
  - XiangShan/Verilator 的第一阶段薄适配层
- Create: `tests/test_run_pipeline.py`
  - 覆盖 CLI seed 解析、ledger 输出、目录布局和 adapter 调用

### Recommended Execution Flow

建议流程：

```text
CLI run request
-> parse seeds
-> create run batch dir
-> for each seed:
   -> load suite
   -> override suite seed
   -> emit/build into seed-specific dir
   -> invoke target adapter
   -> write run_meta.json
-> write run_ledger.json
```

### Recommended Result Labels

第一阶段推荐只保留弱标签：

- `built`
- `ran`
- `timeout`
- `nonzero_exit`
- `trap_seen`
- `suspicious`

避免出现任何强语义标签。

## Dependencies and Sequence

### Milestones

1. Milestone 1: Freeze run-batch interface
   - Phase A: 定义 seed 输入语义与 CLI contract
   - Phase B: 定义 run artifact/ledger schema

2. Milestone 2: Build batch execution plumbing
   - Phase A: 支持 seed-aware artifact 目录
   - Phase B: 支持 batch loop 和 per-seed result capture

3. Milestone 3: Add target execution and verification
   - Phase A: 实现最小 target run adapter
   - Phase B: 增加测试并验证 build-only 路径未退化

### Suggested Task Breakdown

| Task ID | Description | Target AC | Depends On |
|---------|-------------|-----------|------------|
| task1 | Define seed input grammar and run ledger schema for Phase 1 | AC-1, AC-3, AC-4 | - |
| task2 | Add run-related dataclasses and seed-specific artifact path helpers | AC-2, AC-3 | task1 |
| task3 | Implement seed expansion and batch orchestration in a dedicated run module | AC-1, AC-2, AC-3 | task1, task2 |
| task4 | Implement the minimal XiangShan/Verilator target run adapter | AC-1, AC-2 | task3 |
| task5 | Wire `generator/cli.py run` to the new batch execution path | AC-1, AC-5 | task3, task4 |
| task6 | Add tests for seed parsing, ledger generation, per-seed directory isolation, and adapter invocation | AC-1, AC-2, AC-3, AC-5 | task2, task3, task5 |
| task7 | Run the full verification matrix and confirm Phase 1 still avoids semantic overclaiming | AC-4, AC-5 | task4, task5, task6 |

## Implementation Notes

- Keep the first implementation explicitly Phase 1: fixed code, per-seed rebuild, weak labels only.
- Prefer introducing a dedicated run module instead of overloading `toolchain.py` with batch orchestration logic.
- Make the ledger schema easy to extend for later probe/checker fields, but do not populate those fields now.
- Ensure failure cases still emit enough per-seed metadata for postmortem triage.
- Preserve current `build` CLI behavior and artifact layout for non-run workflows.
