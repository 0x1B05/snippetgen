# Vsetvl Interrupt Path Plan

## Goal Description

实现一个最小 path-oriented demo，使 `snippetgen-demo` 能生成并构建一个新的 baremetal suite，该 suite 在程序路径中包含：

- interrupt-related setup
- 真实发出的 `vsetvl zero, zero, zero`

本计划的目标严格限定为：

- 把真实 `vsetvl zero, zero, zero` 纳入现有 snippet 生成链
- 为此新增最小 snippet、manifest、suite 和测试
- 稳定产出 `build/vsetvl_interrupt_path_poc/test.elf` 与 `test.bin`

本计划**不**要求本轮完成：

- 真实 target `run`
- 真实 interrupt 命中验证
- trap 命中验证
- RTL probe/trace 消费
- `/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md` 中 ROB 内部机制验证

## Acceptance Criteria

- AC-1: 新的 path-oriented suite 与 snippet metadata 能被当前生成器稳定解析为确定性的执行计划
  - Positive Tests (expected to PASS):
    - 给定 `suites/vsetvl_interrupt_path_poc.yaml`，工具能解析出固定顺序的 snippet 列表。
    - 同一份 suite 在固定 seed 下重复执行 `dump-plan`，输出的 suite 名、seed、snippet 顺序和 artifact 路径保持一致。
    - 新增 snippet 的 manifest 能被 `snippet_db.py` 正确加载并解析到现有 `SnippetSpec`。
  - Negative Tests (expected to FAIL):
    - path suite 引用不存在的 snippet ID 时，planning 阶段失败并返回明确错误。
    - path suite 使用未支持的 `compose.mode` 时，仍然按现有 contract 以 `future-only` 失败。
    - 新增 manifest 缺少 `id`、`kind`、`lang` 或 `sources` 时，loading 阶段失败并指出具体 manifest。

- AC-2: 新增的 `vsetvl` path snippet 必须在当前 `proc snippet` ABI 下真实发出 `vsetvl zero, zero, zero`，且不扩大全局 toolchain 目标面
  - Positive Tests (expected to PASS):
    - 新增 snippet 在当前全局 `-march=rv64gc` 下可以编译通过。
    - 通过局部 `asm` 片段发出的 `vsetvl zero, zero, zero` 会出现在新 suite 的构建产物反汇编中。
    - 新 checker snippet 能基于 `env` 内的路径标记判断 `vsetvl_interrupt_path` 是否执行到。
  - Negative Tests (expected to FAIL):
    - 如果 `vsetvl_interrupt_path` 没有导出 descriptor，构建必须链接失败。
    - 如果实现只保留路径标记、但最终产物反汇编中没有 `vsetvl`，测试必须失败。
    - 如果实现依赖全局把 toolchain 改成 `rv64gcv` 才能工作，判定为不满足本准则。

- AC-3: 新 suite 的构建链必须稳定产出独立 artifact，且不破坏现有默认 suite 的构建行为
  - Positive Tests (expected to PASS):
    - 执行构建命令后，存在 `build/vsetvl_interrupt_path_poc/generated_suite.c`。
    - 执行构建命令后，存在 `build/vsetvl_interrupt_path_poc/test.elf`。
    - 执行构建命令后，存在 `build/vsetvl_interrupt_path_poc/test.bin`。
    - `build/vsetvl_interrupt_path_poc/build_manifest.json` 中记录 suite 名、seed、snippet 顺序和 compile/link/objcopy 命令。
    - 现有 `scalar_load_legality_poc` suite 的 build 和单元测试继续通过。
  - Negative Tests (expected to FAIL):
    - 如果新 suite 的某个 source 缺失，构建必须失败，不允许产出看似成功的 ELF/bin。
    - 如果 objcopy 失败，不允许保留新的 suite 的成功 artifact 并把任务视为成功。

- AC-4: 新增 checker 和文档必须明确维持 path coverage 边界，不把该 case 伪装成“已验证真实 interrupt 语义”
  - Positive Tests (expected to PASS):
    - 新 checker 只基于 `env` 内的路径标记进行判断，不依赖真实 trap/probe 数据。
    - 新增文档或 plan 中明确说明该 suite 仅覆盖“相关程序路径”，不验证内部 ROB 机制。
    - 现有 `generator/cli.py run` 仍保持未实现状态，不因本轮变更而假装具备 target execution 能力。
  - Negative Tests (expected to FAIL):
    - 如果实现引入“已验证 interrupt 命中”或“已复现 PR 5757 bug”这类结论，但没有 run/probe/checker 支撑，判定为范围越界。
    - 如果为实现该 suite 而额外引入 target adapter、probe schema、coverage summary 或 RTL signal mapping，判定为超出本轮范围。

## Path Boundaries

Path boundaries define the acceptable range of implementation quality and scope for this path-oriented demo.

### Upper Bound (Maximum Acceptable Scope)

最完整但仍然可接受的实现包括：

- 新增一个 `vsetvl_interrupt_path_poc` suite
- 新增 `vsetvl_interrupt_path` snippet 与 `check_vsetvl_interrupt_path` snippet
- 新增对应 manifest
- 新增 build-path tests 和反汇编检查
- 新增一份简短文档，明确 path coverage 边界

这一上界**不**包含：

- XiangShan Verilator run flow
- runtime-backed trap result export
- probe schema / probe map / coverage JSON
- 与 ROB 内部信号对应的 checker

### Lower Bound (Minimum Acceptable Scope)

最小可接受实现包括：

- 能加载一个新 suite `vsetvl_interrupt_path_poc`
- 能把一个包含真实 `vsetvl zero, zero, zero` 的 snippet 编进最终 ELF
- 能产出 `generated_suite.c`、`test.elf`、`test.bin`
- 能通过一个最小 checker 证明相关程序路径执行到

只要缺少其中任意一项，就不算完成本计划。

### Allowed Choices

- Can use:
  - 现有 `proc snippet` ABI
  - C snippet with local inline asm
  - 现有 manifest/suite schema
  - 现有 `env` 字段与 path marker
  - 现有 build pipeline 与测试框架
  - 反汇编检查最终 ELF 中是否出现 `vsetvl`
- Cannot use:
  - 把全局 toolchain 默认目标直接升级为 vector-enabled target
  - 实现 target `run` 或宣称已具备真实运行验证
  - 引入 probe catalog、coverage summary、adaptive loop
  - 把该 suite 描述成“已验证 interrupt 命中窗口”或“已复现 ROB bug”

## Feasibility Hints and Suggestions

> Note: This section is for reference and understanding only. These are implementation suggestions, not prescriptive file-by-file instructions.

### Recommended Implementation Shape

尽管 draft 提到了纯 `.S` snippet，更推荐的实现是：

- 用一个新的 C snippet 文件定义 descriptor 和 `run/check` 逻辑
- 在 `run()` 内使用局部 inline asm：
  - `.option push`
  - `.option arch, +v`
  - `vsetvl zero, zero, zero`
  - `.option pop`

这样做的好处是：

- 保持与当前 snippet 风格一致
- 不必为纯 `.S` snippet 单独处理 descriptor 数据布局
- 不必扩 manifest schema 去表达 mixed-source snippet
- 仍然可以在最终产物里得到真实 `vsetvl`

### Marker Strategy

建议给新路径使用独立 marker，而不是复用现有 `scalar_load_legality` 的状态位：

- 一个 marker 表示“已进入 `vsetvl_interrupt_path`”
- 一个 marker 表示“已完成 `vsetvl_interrupt_path`”

这些 marker 应放在当前 `env` 可承载的范围内，例如：

- `env.flags` 的未使用位
- 或 `env.snippet_id` / `env.test_id` 的专用 magic 值

推荐优先用 `env.flags` 的新位，避免和现有默认 suite 的语义混淆。

### Verification Strategy

建议不要把验证停留在“源码里有 asm 字符串”这一级，而是增加一个 build 后检查：

- 对 `build/vsetvl_interrupt_path_poc/test.elf` 做反汇编
- 断言输出里确实存在 `vsetvl`

这样可以锁住“真实指令被编进最终产物”这个目标，而不是只锁源码意图。

## Dependencies and Sequence

### Milestones

1. Milestone 1: Freeze the path-oriented contract
   - Phase A: 确定新 suite 名称、snippet 顺序和 path coverage 边界
   - Phase B: 确定 marker 方案与 checker 只检查本地 path markers

2. Milestone 2: Add the new path snippets and metadata
   - Phase A: 实现 `vsetvl_interrupt_path`，用局部 asm 发出真实 `vsetvl`
   - Phase B: 实现 `check_vsetvl_interrupt_path`，并新增 manifest 与 suite YAML

3. Milestone 3: Wire the build and verification path
   - Phase A: 增加新 suite 的 loader/emitter/build tests
   - Phase B: 增加最终 ELF 反汇编检查和默认 suite 非回归验证

### Suggested Task Breakdown

| Task ID | Description | Target AC | Depends On |
|---------|-------------|-----------|------------|
| task1 | Define the path marker contract and the final suite order for `vsetvl_interrupt_path_poc` | AC-1, AC-4 | - |
| task2 | Implement `vsetvl_interrupt_path` as a C snippet with local inline asm that emits `vsetvl zero, zero, zero` and updates path markers | AC-2 | task1 |
| task3 | Implement `check_vsetvl_interrupt_path` and any shared constants needed for marker validation | AC-2, AC-4 | task1 |
| task4 | Add the new manifests and `suites/vsetvl_interrupt_path_poc.yaml` | AC-1, AC-3 | task2, task3 |
| task5 | Extend tests for suite loading, manifest loading, harness generation, and build artifacts for the new suite | AC-1, AC-3 | task4 |
| task6 | Add a post-build disassembly assertion that the final ELF contains `vsetvl` | AC-2 | task4 |
| task7 | Run the existing scalar suite verification matrix plus the new suite verification matrix and confirm no scope creep landed | AC-3, AC-4 | task5, task6 |

## Implementation Notes

- Code and comments must not claim that this suite proves real interrupt delivery or reproduces the XiangShan ROB bug.
- Keep the global toolchain default unchanged unless a change is separately justified and reviewed; the preferred path is local inline asm that temporarily enables `+v`.
- Reuse existing emitter, loader, and manifest patterns rather than inventing a new snippet type.
- Prefer adding a small helper for marker bits if it improves readability, but do not expand the runtime ABI just for this suite.
- Tests should verify behavior at the artifact level when possible, especially the final-ELF `vsetvl` check.
- Do not add run/probe/checker framework layers in this plan; those belong to a later scope if the user wants full bug-mechanism validation.
