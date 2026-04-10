# Vsetvl Interrupt Path Draft

## Goal

在当前 `snippetgen-demo` 框架内，先落一个**可构建、可运行到 baremetal ELF** 的最小 draft，用来覆盖：

- 程序路径里出现真实的 `vsetvl zero, zero, zero`
- 路径上保留“interrupt 相关前置动作”

本 draft 的目标是 **path coverage**，不是验证 `/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md` 中分析到的 ROB 内部错账机制。

## Conclusion

当前框架下，下面这件事是可行的：

- 制作一个 baremetal snippet suite，包含 `arm_timer` 和真实发出 `vsetvl zero, zero, zero` 的新 snippet

当前框架下，下面这件事暂时不可行：

- 用框架直接验证 `flushAfter + flushSelf`
- 直接验证 `hasCommitted(0)`、`enqPtr`、`deqPtr`
- 直接证明中断命中在 `vsetvl zero, zero, zero` 这条指令窗口上发生

原因不是单个 snippet 缺失，而是当前 demo 还没有：

- target `run` 层
- 可消费的 RTL probe/trace 抽象
- scenario expectation/checker 机制
- semantic probe 到内部信号的映射层

## Recommended Draft

推荐先实现一个最小 path-oriented suite：

```text
init_basic_env
-> arm_timer
-> vsetvl_interrupt_path
-> check_vsetvl_interrupt_path
-> finish_check
```

### Snippet 1: `vsetvl_interrupt_path`

职责：

- 记录“已经进入 vector/interrupt 相关路径”
- 发出真实的 `vsetvl zero, zero, zero`
- 可重复执行若干次，扩大潜在 interrupt 窗口
- 记录“已经完成该路径”

建议实现方式：

- 用 `.S` snippet，而不是 C inline asm
- 在 snippet 局部使用 `.option arch, +v`
- 保持 toolchain 全局默认 `-march=rv64gc` 不变，避免扩大当前 demo 的目标面

建议骨架：

```asm
.text
.globl snippet_vsetvl_interrupt_path_run
snippet_vsetvl_interrupt_path_run:
  # mark entered
  # repeat:
  .option arch, +v
  vsetvl zero, zero, zero
  # mark exited
  ret
```

### Snippet 2: `check_vsetvl_interrupt_path`

职责：

- 检查 path 标记是否被置位
- 确认 `vsetvl_interrupt_path` 的 run 阶段确实执行到

这一步只做程序路径自检，不声称验证到了：

- interrupt arrival timing
- trap taken
- ROB redirect 行为
- 文档中的内部 bug 机制

## Required Repository Changes

建议新增：

- `snippets/vector_interrupt/vsetvl_interrupt_path.S`
- `snippets/vector_interrupt/check_vsetvl_interrupt_path.c`
- `snippets/manifests/vsetvl_interrupt_path.yaml`
- `snippets/manifests/check_vsetvl_interrupt_path.yaml`
- `suites/vsetvl_interrupt_path_poc.yaml`

建议测试补充：

- suite loader 能解析新 suite
- manifest loader 能接受 `lang: asm`
- emitter 能把新 snippet 接进 harness
- `build` 能稳定产出 `build/vsetvl_interrupt_path_poc/test.elf`
- `build` 能稳定产出 `build/vsetvl_interrupt_path_poc/test.bin`

## Draft Acceptance Boundary

这版 draft 成功后，可以宣称：

- 生成链能产出包含真实 `vsetvl zero, zero, zero` 的 baremetal ELF
- suite 中包含 interrupt-related setup 与 vector path snippet
- 当前框架已经能表达“触发相关程序路径”的最小 case

这版 draft 不能宣称：

- XiangShan 一定在该窗口对 interrupt 响应
- 该 case 一定能复现 PR 5757 对应 bug
- 已验证 `vsetvl zero, zero` 被错误分类为 `interrupt_safe`
- 已验证 `enqPtr/deqPtr` overtake

## Framework Gaps For Full Bug Validation

如果后续要把这个 draft 升级成“验证文档里分析到的机制”，至少需要补下面几类能力。

### 1. Run Layer

需要一个真实 `run` 子命令或 target adapter：

- 把生成的 ELF 送进 XiangShan/Verilator
- 统一处理运行命令、退出码、日志和产物目录

### 2. Probe Schema

需要定义 scenario 级别的 probe 需求，而不是只靠 snippet 内部 flag：

- redirect kind
- interrupt response marker
- ROB head metadata
- dequeue bookkeeping marker
- enqueue/dequeue pointer-related observables

### 3. Probe Mapping

需要把语义 probe 映射到当前 XiangShan 可观测源：

- RTL signal
- trace log
- difftest side channel
- post-run decoder

### 4. Checker Layer

需要一个 checker，能对 scenario 给出“命中/未命中”判定，而不是只看 snippet 是否 return 0：

- 是否发生了 interrupt-related redirect
- 是否出现了 `flushAfter` 与 `flushSelf` 的混合
- 是否出现了与文档一致的错误轨迹

### 5. Stronger Runtime

当前 runtime 的 timer/trap/platform 基本还是 stub。若要把 case 提升到真实 interrupt 语义验证，至少要补：

- 可安装并真正生效的 trap entry
- 与目标平台一致的 timer arm/enable 语义
- 最小可用的 trap handler convention
- 运行后把 trap/probe 结果导出给 host 侧

## Recommendation

建议按两阶段推进：

1. 先落这个 path-oriented draft
   - 目标是把真实 `vsetvl zero, zero, zero` 纳入 snippet 生成链
   - 证明框架已经能承载“vector + interrupt-related setup”的最小路径
2. 再立一个后续需求文档
   - 专门扩 `run/probe/checker`
   - 把“触发相关路径”升级到“验证内部机制”

## Final Position

基于当前 `snippetgen-demo` 的抽象边界，这个 draft 是合理且可落地的第一步。

它不会过度承诺“已经验证 bug 机制”，但能把最关键的真实程序元素先纳入生成链：

- baremetal
- suite-driven
- real `vsetvl zero, zero, zero`
- interrupt-related setup
