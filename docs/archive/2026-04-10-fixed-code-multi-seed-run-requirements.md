# Fixed-Code Multi-Seed Run Requirements

## Goal

在 `snippetgen-demo` 中，为现有固定测试程序建立一个“多 seed 重复执行”的最小闭环。

这里的“固定代码”指：

- suite 结构固定
- snippet 集合固定
- 程序路径固定

这里的“多 seed 重复执行”指：

- 对同一测试意图，使用多个 seed 重复生成并运行
- 记录每次运行的输入参数、产物和结果
- 让后续分析可以基于 seed 分布，而不是单次手工试跑

本需求的第一目标不是“证明已经复现某个内部 bug”，而是把：

- seed
- build
- run
- result ledger

这条链路先做实。

## Why This Phase Comes First

如果目标最终是尽量覆盖 `/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md` 中分析的真实场景，仅靠当前“生成 ELF + 静态检查反汇编”还不够。

至少还需要：

- 多次执行
- 每次执行的 seed 管理
- 运行结果归档
- 后续可接 probe/checker 的稳定接口

因此，第一阶段先不做随机代码生成，而做“固定代码、多 seed 重复执行”是更稳妥的路径。

## Scope

### In Scope

- 固定 suite 的多 seed 执行
- `run` 子命令的最小落地
- 每次 seed 对应的 build/run/result 记录
- 运行结果 ledger
- 面向后续 probe/checker 的结果 schema 预留

### Out of Scope

- 随机代码生成
- snippet/random mixing
- 自适应闭环再生成
- 真实内部 RTL 语义判定
- `flushAfter` / `flushSelf` / `hasCommitted` / `enqPtr` / `deqPtr` 的直接验证
- 覆盖率收敛算法

## Core Requirement

系统必须支持：

1. 选择一个固定 suite
2. 给定多个 seed
3. 对每个 seed 执行：
   - build
   - run
   - result capture
4. 生成一个 machine-readable ledger

该 ledger 必须允许后续回答：

- 哪些 seed 被执行过
- 每个 seed 的 ELF 是什么
- 每个 seed 的 run 结果是什么
- 哪些 seed 出现了异常或可疑行为

## Phase 1 Execution Model

### Recommended Model

第一阶段推荐采用：

```text
seed
-> build one ELF for that seed
-> run that ELF
-> record result
```

即：

- 代码逻辑固定
- 每个 seed 生成一个对应 ELF
- 不要求“同一个 ELF 支持多 seed 注入”

### Why This Model

因为当前框架里：

- `seed` 已经自然进入 build/emitter 路径
- baremetal runtime 还没有成型的 host-to-target 参数注入协议
- 先做“每 seed 一个 ELF”成本最低、路径最清晰

## CLI Requirements

至少新增一个真实可用的 `run` 入口。

### Minimum CLI Shape

建议支持以下形态：

```bash
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed 1234
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seeds 1,2,3,4
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed-range 0:99
python3 generator/cli.py run suites/vsetvl_interrupt_path_poc.yaml --seed-range 0:99 --repeat 3
```

### Minimum Behavior

对于每个 seed：

- build 对应 artifact
- 调用 target run adapter
- 等待完成、失败或超时
- 记录结果

## Target Run Adapter Requirements

第一阶段需要一个最小 target run adapter，但要求尽量薄。

它至少要负责：

- 接收 ELF 路径
- 调起 XiangShan/Verilator 运行
- 返回 exit status
- 保存 stdout/stderr/log
- 生成最小 run result

第一阶段不要求它解释内部语义，只要求它能稳定地“跑”和“收结果”。

## Result Ledger Requirements

每次多 seed run 必须产出一个 ledger 文件。

### Recommended Location

建议放在：

```text
build/<suite>/runs/<timestamp>/
```

### Recommended Files

- `run_ledger.json`
- `seed_<N>/test.elf`
- `seed_<N>/test.bin`
- `seed_<N>/stdout.log`
- `seed_<N>/stderr.log`
- `seed_<N>/run_meta.json`

## Recommended Ledger Schema

```json
{
  "suite": "vsetvl_interrupt_path_poc",
  "run_batch": "2026-04-10T15:00:00Z",
  "target": "xiangshan-verilator",
  "entries": [
    {
      "seed": 1234,
      "artifact_dir": "...",
      "elf": "...",
      "bin": "...",
      "status": "pass|fail|timeout|error|unknown",
      "stdout_log": "...",
      "stderr_log": "...",
      "labels": ["built", "ran"],
      "notes": ""
    }
  ]
}
```

第一阶段里 `labels` 可以先很弱，例如：

- `built`
- `ran`
- `timeout`
- `trap_seen`
- `nonzero_exit`
- `suspicious`

## Hit Classification Requirements

第一阶段必须明确：

- 不能把任何 run result 直接称为“复现了目标 bug”
- 只能做“弱命中分类”

### Allowed Weak Labels

- `path_executed`
- `trap_seen`
- `unexpected_exit`
- `timeout`
- `suspicious`

### Disallowed Claims

第一阶段禁止直接输出：

- “已复现文档中的 bug”
- “已证明 interrupt 命中在目标指令窗口”
- “已验证 ROB 内部错账”

除非后续 probe/checker 层已经落地。

## Relationship With Current `vsetvl_interrupt_path_poc`

该需求默认以现有：

- `vsetvl_interrupt_path_poc`

作为第一批固定代码 case。

理由：

- 它已经具备最小路径
- 已有真实 `vsetvl`
- 已有 interrupt-related setup
- 很适合做“多 seed 重复执行”基础样本

## Future Compatibility Requirements

Phase 1 的 run/ledger 设计必须为后续能力预留接口：

### Phase 2 Planned Extensions

- probe extraction
- semantic checker
- seed-level hit classification
- 可疑 seed 自动重跑
- 可疑 seed 的额外日志/波形采集

因此第一阶段虽然不实现这些能力，但 ledger schema 和目录结构不应把这些扩展堵死。

## Acceptance Criteria

### AC-1

固定 suite 支持多 seed run 批执行。

Positive:

- 对一个固定 suite 指定多个 seed，系统能逐个 build 和 run。

Negative:

- seed 参数非法时，CLI 明确失败。

### AC-2

每个 seed 都产出独立 artifact 与独立 run record。

Positive:

- 每个 seed 都有独立目录和独立 meta。

Negative:

- 不允许不同 seed 共享同一个未标记 seed 的结果目录。

### AC-3

批量运行必须生成 machine-readable ledger。

Positive:

- ledger 可以列出全部 seed 及对应结果。

Negative:

- run 完成后只留 stdout 文本、没有结构化 ledger，判定为失败。

### AC-4

系统必须区分“运行结果”与“语义命中”。

Positive:

- 第一阶段输出只使用弱标签，不声称复现内部机制。

Negative:

- 没有 probe/checker 却输出“已复现文档场景”，判定为失败。

## Recommended Next Step

基于这份需求，下一步建议先写实现计划，而不是直接改代码。

因为一旦引入 `run`，就会涉及：

- target adapter 边界
- 目录布局
- ledger schema
- seed 批处理语义
- 超时和失败策略

这些都值得先冻结。
