# SnippetGen ELF-First PoC Detail Plan

## Goal Description

实现一个**最小可执行 PoC**，证明 `SnippetGen` 这条基础链路成立：

- 读取 `suite.yaml`
- 读取 `snippet manifests`
- 定位 `snippet` 源文件
- 自动生成 harness
- 用 RISC-V 交叉工具链编译并链接出 `ELF`
- 从 `ELF` 导出 `bin`

本计划的目标**严格限制**为生成 `ELF/bin` 文件，不要求本轮完成 Verilator 运行、probe 回传、coverage 统计或 adaptive regeneration。实现必须围绕 `XiangShan + Verilator + 现有 difftest 环境`，但第一阶段的“完成”只以构建链打通为准。

## Acceptance Criteria

Following TDD philosophy, each criterion includes positive and negative tests for deterministic verification.

- AC-1: Suite 和 snippet metadata 能被稳定解析为一个确定性的执行计划
  - Positive Tests (expected to PASS):
    - 给定 `snippetgen-demo/suites/scalar_load_legality_poc.yaml`，工具能解析出按顺序排列的少量 snippet ID，并保持顺序稳定。
    - 同一份 suite 在固定 seed 下重复执行 `dump-plan`，输出的 snippet 顺序、目标信息、产物路径完全一致。
  - Negative Tests (expected to FAIL):
    - suite 中引用不存在的 snippet ID 时，构建在 planning 阶段失败，并返回明确错误。
    - snippet manifest 缺少 `id` 或 `sources` 字段时，构建在 loading 阶段失败，并指出具体 manifest 文件。
  - AC-1.1: 解析后的执行计划必须只支持 `sequence` 组合模式
    - Positive:
      - `compose.mode: sequence` 被接受并生成计划。
    - Negative:
      - `compose.mode: weighted-mix` 或任何未支持模式被拒绝，并提示“future-only”而不是隐式降级。

- AC-2: 生成器能自动发射最小 harness C 文件，并将 runtime 与 snippets 接入同一个编译目标
  - Positive Tests (expected to PASS):
    - 执行构建命令后，`build/<suite>/generated_suite.c` 被创建，且内容包含按顺序调用 snippet 的入口逻辑。
    - 生成的 harness 能成功引用 `xsrt_env_t`、`xsrt_snippet_desc_t`、以及每个 snippet 的 descriptor 符号。
  - Negative Tests (expected to FAIL):
    - 若某个 snippet 源文件存在但未导出 descriptor，harness 生成或链接时失败，不允许静默跳过。
    - 若 generator 未找到 runtime 头文件路径，编译必须失败，不允许退化成手写空 main。
  - AC-2.1: Harness 生成必须是自动的，而不是仓库里预置一份固定 main
    - Positive:
      - 修改 suite 顺序后重新 build，`generated_suite.c` 内容发生对应变化。
    - Negative:
      - 若不读取 suite、仅使用硬编码 snippet 顺序，也能得到相同结果，则判定为不满足本准则。

- AC-3: 最小 runtime 和 snippet ABI 足以支撑 PoC 构建
  - Positive Tests (expected to PASS):
    - 头文件中存在最小 C API：`xsrt_init`、`xsrt_finish_pass`、`xsrt_finish_fail`、`xsrt_csr_read`、`xsrt_csr_write`、`xsrt_install_strap`、`xsrt_enable_stimer`、`xsrt_timer_arm_delta`。
    - `xsrt_snippet_desc_t` ABI 被定义，5 个最小 snippet 都能按统一 ABI 编译通过。
  - Negative Tests (expected to FAIL):
    - 若 snippet 直接依赖未冻结的高级 API（例如 MMU/HYP/probe catalog 运行时解析），第一阶段构建应失败或被 lint 阻止。
    - 若 snippet 之间必须依赖隐式寄存器状态才能通过编译或链接，判定为 ABI 设计不合格。
  - AC-3.1: 第一阶段 snippet 仅支持 `proc snippet`
    - Positive:
      - `kind: proc` manifest 被接受。
    - Negative:
      - `kind: stream` manifest 被拒绝，并明确标注“not implemented in ELF-first PoC”。

- AC-4: 构建系统能稳定产出 `ELF/bin`
  - Positive Tests (expected to PASS):
    - 构建完成后存在 `build/scalar_load_legality_poc/test.elf`。
    - 构建完成后存在 `build/scalar_load_legality_poc/test.bin`。
    - `build/scalar_load_legality_poc/build_manifest.json` 中记录 suite 名、seed、snippet 顺序和编译命令。
  - Negative Tests (expected to FAIL):
    - 如果链接阶段缺少任何一个 runtime/snippet/object，构建必须失败，不允许产出不完整的 ELF。
    - 如果 `objcopy` 失败，不允许只保留 ELF 并把整体任务视为成功。
  - AC-4.1: 产物路径和命名必须可预测
    - Positive:
      - 在默认配置下，产物始终位于 `build/<suite>/`。
    - Negative:
      - 同一 suite 因临时路径、随机命名或未记录的中间目录导致产物位置漂移，视为失败。

## Path Boundaries

Path boundaries define the acceptable range of implementation quality and choices.

### Upper Bound (Maximum Acceptable Scope)

最完整但仍然可接受的第一阶段实现包括：
- `snippetgen-demo/` 完整目录骨架
- 最小 runtime
- 最小 snippet ABI
- 5 个最小 snippet
- suite/manifest 解析器
- harness emitter
- toolchain wrapper
- `ELF/bin` 产物和 `build_manifest.json`
- 基础单元测试覆盖 loader / emitter / path resolution

这一上界**不**包含 Verilator 运行、probe JSON、coverage bins、adaptive regeneration。

### Lower Bound (Minimum Acceptable Scope)

最小可接受实现包括：
- 能解析一个 suite YAML
- 能找到对应 snippet manifests 与源文件
- 能自动生成一个 harness 文件
- 能编译出 `test.elf`
- 能导出 `test.bin`

只要缺少其中任意一环，就不算完成第一阶段。

### Allowed Choices

- Can use:
  - Python 3
  - YAML
  - Makefile
  - RISC-V baremetal C/assembly
  - 显式路径配置
  - 直接生成 `generated_suite.c`
  - 交叉编译器命令行封装
- Cannot use:
  - 在第一阶段引入随机 instruction generator
  - 在第一阶段实现 snippet/random mixing
  - 在第一阶段把 probe/coverage 作为成功标准
  - 依赖隐式寄存器协商作为 snippet 组合机制
  - 手工维护固定 main/harness 来冒充“自动生成”

> **Note on Deterministic Designs**: 本阶段设计是强约束、低自由度设计。`target` 固定，`compose.mode` 固定为 `sequence`，`kind` 固定只支持 `proc`。因此上界和下界在方向上非常接近，差别只在工程完整度而不在架构分叉。

## Feasibility Hints and Suggestions

> **Note**: This section is for reference and understanding only. These are conceptual suggestions, not prescriptive requirements.

### Conceptual Approach

建议用“单向发射”的方式做第一阶段：

1. `snippet_db.py` 扫描 `snippets/manifests/*.yaml`
2. `suite_loader.py` 读取 `suite.yaml`
3. `emitter.py` 生成 `generated_suite.c`
4. `toolchain.py` 统一发起：
   - runtime `.c`
   - runtime `.S`
   - snippet `.c/.S`
   - harness `.c`
   - link -> `test.elf`
   - objcopy -> `test.bin`

推荐的 harness 形态：

```c
int main(void) {
  xsrt_env_t env;
  xsrt_init(&env);

  xsrt_run_snippet(&env, &snippet_init_basic_env);
  xsrt_run_snippet(&env, &snippet_arm_timer);
  xsrt_run_snippet(&env, &snippet_unaligned_load);
  xsrt_run_snippet(&env, &snippet_check_scalar_load_legality);
  xsrt_run_snippet(&env, &snippet_finish_check);

  xsrt_finish_pass(&env);
  return 0;
}
```

其中 `xsrt_run_snippet` 可以只是一个很薄的 helper，内部依次调 `init/run/check/fini`。

### Relevant References

- [docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md](/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-poc-elf-first-execution-prep.md) - 本轮 PoC 范围和 ELF-first 目标
- [docs/plans/2026-04-09-xsgen-scalar-load-legality-demo-plan-draft.md](/home/dfpmts/XS/framework/docs/plans/2026-04-09-xsgen-scalar-load-legality-demo-plan-draft.md) - 更完整的后续演进方向
- [nexus-am/README.md](/home/dfpmts/XS/framework/nexus-am/README.md) - baremetal runtime 风格参考
- [riscv-dv/yaml/base_testlist.yaml](/home/dfpmts/XS/framework/riscv-dv/yaml/base_testlist.yaml) - suite/testlist 风格参考
- [riscv-dv/src/riscv_directed_instr_lib.sv](/home/dfpmts/XS/framework/riscv-dv/src/riscv_directed_instr_lib.sv) - directed block 作为未来 mixing 的接口参考
- [STING_User_Guide.pdf](/home/dfpmts/XS/framework/STING_Manual_2025/STING_User_Guide.pdf) - snippet/resource/rendering 设计参考

## Dependencies and Sequence

### Milestones

1. Milestone 1: Freeze minimal interfaces and file layout
   - Phase A: 定义 `xsrt_env_t` 与最小 runtime C API
   - Phase B: 定义 `xsrt_snippet_desc_t`、snippet manifest schema、suite schema

2. Milestone 2: Make generation deterministic
   - Phase A: 实现 manifest/suite loader
   - Phase B: 实现 deterministic `ComposePlan`

3. Milestone 3: Emit and build
   - Phase A: 发射 `generated_suite.c`
   - Phase B: 用 toolchain wrapper 编译、链接并导出 `ELF/bin`

4. Milestone 4: Add execution-prep artifacts
   - Phase A: 写入 `build_manifest.json`
   - Phase B: 用最小单元测试锁住 loader / emitter / path resolution 行为

## Task Breakdown

Each task must include exactly one routing tag:
- `coding`: implemented by Claude
- `analyze`: executed via Codex (`/humanize:ask-codex`)

| Task ID | Description | Target AC | Tag (`coding`/`analyze`) | Depends On |
|---------|-------------|-----------|----------------------------|------------|
| task1 | Create `snippetgen-demo/` skeleton with top-level `Makefile`, `README.md`, and empty runtime/snippets/generator/suites directories | AC-4 | coding | - |
| task2 | Implement minimal runtime headers and source stubs for env, CSR, trap, timer, finish helpers | AC-3 | coding | task1 |
| task3 | Define `xsrt_snippet_desc_t` and a helper runner for `init/run/check/fini` calling convention | AC-2, AC-3 | coding | task2 |
| task4 | Implement the 5 PoC snippets and their manifests: `init_basic_env`, `arm_timer`, `unaligned_load`, `check_scalar_load_legality`, `finish_check` | AC-1, AC-3 | coding | task3 |
| task5 | Implement Python data models for `SnippetSpec`, `SuiteSpec`, `ComposePlan`, and `BuildArtifact` | AC-1 | coding | task1 |
| task6 | Implement `snippet_db.py` to scan manifests, validate required fields, and resolve source file paths | AC-1 | coding | task5 |
| task7 | Implement `suite_loader.py` to load `scalar_load_legality_poc.yaml`, validate `sequence` mode, and produce a deterministic plan | AC-1 | coding | task5 |
| task8 | Implement `emitter.py` to generate `build/<suite>/generated_suite.c` from the ordered snippet list | AC-2 | coding | task6, task7 |
| task9 | Implement `toolchain.py` to compile runtime/snippet/harness sources, link `test.elf`, and export `test.bin` | AC-4 | coding | task2, task4, task8 |
| task10 | Create `scalar_load_legality_poc.yaml` and verify the build path generates `test.elf`, `test.bin`, and `build_manifest.json` | AC-1, AC-4 | coding | task9 |
| task11 | Add unit tests for manifest loading, suite loading, and harness emission failure modes | AC-1, AC-2 | coding | task6, task7, task8 |
| task12 | Review produced artifacts and prune any code that accidentally depends on future-only concepts like mixing, probe catalogs, or adaptive loops | AC-3, AC-4 | analyze | task10, task11 |

## Claude-Codex Deliberation

### Agreements

- 第一阶段必须只盯住 `ELF/bin` 产出，不把 Verilator 执行和 probe 回传作为 gating 条件。
- runtime、snippet ABI、Python generator 三层必须从第一天就拆开，避免把目标机行为和宿主机构建逻辑耦合。
- suite 组合模式在第一阶段必须固定为 `sequence`，但内部数据模型要为未来 mixing 留接口。

### Resolved Disagreements

- Scope breadth: 一开始的较大 draft 包含 probe catalog、scenario catalog、target adapter、运行后 coverage 输出；本次 detail plan 选择保留这些作为**后续接口方向**，但不作为第一阶段必做项。理由是当前用户明确要求“只要一个 poc”，且第一目标是稳定生成 `ELF/bin`。

### Convergence Status

- Final Status: `converged`

## Resolved User Decisions

- DEC-1: 正式实现目录名
  - Claude Position: 使用 `snippetgen-demo/`，使目录名和项目目标保持一致。
  - Codex Position: 无额外异议。
  - Tradeoff Summary: 新名字更直观，且当前仍在 PoC 早期，改名成本很低。
  - Decision Status: `snippetgen-demo`

- DEC-2: 第一阶段 snippet 数量控制
  - Claude Position: 维持极少数量的 snippet，仅保留证明链路所需的最小集合。
  - Codex Position: 无额外异议。
  - Tradeoff Summary: snippet 越少，manifest、loader、emitter、toolchain 的调试面越小，更有利于尽快拿到第一个 `ELF/bin`。
  - Decision Status: `Keep the snippet set minimal; start with 5 and reduce if any snippet is redundant`

## Implementation Notes

### Code Style Requirements

- Implementation code and comments must NOT contain plan-specific terminology such as "AC-", "Milestone", "Step", "Phase", or similar workflow markers
- These terms are for plan documentation only, not for the resulting codebase
- Use descriptive, domain-appropriate naming in code instead
- 第一阶段代码里不要提前出现 `mix`, `weighted`, `adaptive`, `closed_loop` 这类 future-only 路径判断，除非只是注释说明未来扩展点

### Additional Notes For This PoC

- `detail-plan.md` 的成功条件是 `ELF/bin` 产出，不是仿真通过。
- 如果构建链中需要目标相关 linker script 或 platform-specific finish stub，应优先把它们收敛进 `runtime/platform/xiangshan/`，不要散落在 snippets 目录。
- `build_manifest.json` 是第一阶段的重要工件，因为它为后续接 Verilator run、probe decode、coverage summary 提供稳定的中间接口。
