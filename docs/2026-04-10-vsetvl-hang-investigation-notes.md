# 2026-04-10 `vsetvl` Hang Investigation Notes

## 目标

本轮工作的目标分两步：

1. 先确认 `snippetgen-demo` 生成的 baremetal workload 在 XiangShan `emu` 上能够真正响应 timer interrupt，而不是只走本地软件 stub。
2. 在确认真实 interrupt 路径成立后，修改 workload 形态，推动 `vsetvl zero, zero, zero` 相关 case 接近文档中分析的 `enqPtr/deqPtr` 异常，优先观察：
   - XiangShan 内部断言
   - `bad trap`
   - 超时/长时间不收敛

参考分析文档：

- [/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md](/home/dfpmts/XS/kmh-v2/docs/vsetvl-interrupt-deqptr-final-2026-04-09.md)

## 关键结论

### 1. 真实 timer interrupt 已经打通

此前 `snippetgen-demo` 的 timer/trap 只是 stub：

- [runtime/src/xsrt_intr.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_intr.c)
- [runtime/src/xsrt_trap.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_trap.c)
- [runtime/arch/riscv64/trap.S](/home/dfpmts/XS/framework/snippetgen-demo/runtime/arch/riscv64/trap.S)
- [snippets/scalar_load_legality/arm_timer.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/arm_timer.c)

现在已经实现了最小的 M-mode machine-timer interrupt 路径，并新增了一个专门验证它的 suite：

- [suites/interrupt_response_poc.yaml](/home/dfpmts/XS/framework/snippetgen-demo/suites/interrupt_response_poc.yaml)

在真实 XiangShan `emu` 上运行它，结果为 `HIT GOOD TRAP`，并且该 suite 的 check 只有在下面条件成立时才通过：

- `interrupt_count > 0`
- `last_trap_cause == MTIP`
- `last_trap_epc != 0`

因此可以确认：处理器会响应真实 timer interrupt。

### 2. baseline `vsetvl_interrupt_path_poc` 仍然是正常结束

在接入真实 interrupt 路径之后，旧的 baseline：

- [suites/vsetvl_interrupt_path_poc.yaml](/home/dfpmts/XS/framework/snippetgen-demo/suites/vsetvl_interrupt_path_poc.yaml)

继续表现为 `HIT GOOD TRAP`。这说明仅仅“有真实 interrupt + 一小段 `vsetvl` 循环”还不足以把 case 推到异常状态。

### 3. 更激进的 search workload 已经能把 case 推离正常路径

为了更贴近文档里“围着同一个目标 `vsetvl zero, zero, zero` 压 interrupt 窗口”的思路，新增了搜索版 workload：

- [suites/vsetvl_interrupt_search_poc.yaml](/home/dfpmts/XS/framework/snippetgen-demo/suites/vsetvl_interrupt_search_poc.yaml)
- [snippets/vector_interrupt/vsetvl_interrupt_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/vector_interrupt/vsetvl_interrupt_search.c)
- [snippets/vector_interrupt/check_vsetvl_interrupt_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/vector_interrupt/check_vsetvl_interrupt_search.c)

搜索版经历了两个阶段：

1. 早期版本：每轮重 arm timer，再打一次 `vsetvl`
2. 当前版本：**先 arm 一次较小 timer，再进入大量 `vsetvl zero, zero, zero` 密集循环**

第二种更接近这次讨论里确认的方法：

- 先设一个小而合理的 timer interrupt
- 然后通过循环加入很多 `vsetvl zero, zero, zero`

### 4. 已观测到主 ROB 指针不变量断言

在当前 one-shot timer + dense `vsetvl` 模型下，`seed = 0x1234` 的搜索 workload 不再是 `good trap`，而是直接命中 XiangShan 内部断言：

- `Assertion failed at /home/dfpmts/XS/xs-env/XiangShan/build/rtl/Rob.sv:87867`

该断言对应的真实条件已经定位到：

- [Rob.sv](/home/dfpmts/XS/xs-env/XiangShan/build/rtl/Rob.sv#L69234)
- [Rob.scala](/home/dfpmts/XS/xs-env/XiangShan/src/main/scala/xiangshan/backend/rob/Rob.scala#L1287)

即：

- `isBefore(enqPtr, deqPtr) && !isFull(enqPtr, deqPtr)`
- 文本含义是：`deqPtr is older than enqPtr!`

这与分析文档中的核心异常：

- `enqPtr < deqPtr && !isFull`

是直接对上的。

### 5. 还没有确认“真正卡死”

虽然已经观测到：

- `good trap`
- `bad trap`
- ROB 内部断言
- 某些 seed 的长时间超时

但当前还不能严谨地说“已经复现真正卡死”。

原因：

- 某些 seed 的 `timeout` 仍可能是 host-time 边界，而不是微结构永不收敛
- 当前最强证据是 `seed=0x1234` 触发了主 ROB 的指针不变量断言
- `seed=0xffff` 在 `--timeout-sec 180` 下是 `timeout`，但 stdout 为空，仍需要波形或更细粒度 trace 去确认是否真的是 hang

## 本次做出的代码改动

### 运行与链接对齐

为了让 workload 真正能在 XiangShan `emu` 上跑通，先前已经完成这些基础对齐：

- [runtime/arch/riscv64/start.S](/home/dfpmts/XS/framework/snippetgen-demo/runtime/arch/riscv64/start.S)
  - `main` 返回后发出 XiangShan/noop halt trap，而不是死循环
- [runtime/platform/xiangshan/section.ld](/home/dfpmts/XS/framework/snippetgen-demo/runtime/platform/xiangshan/section.ld)
  - 使用平台 linker script
- [generator/xsgen/toolchain.py](/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/toolchain.py)
  - build 使用 linker script
  - 编译参数对齐到更适合实际运行的设置
- [targets/xiangshan-verilator/run_target.py](/home/dfpmts/XS/framework/snippetgen-demo/targets/xiangshan-verilator/run_target.py)
  - 通过 `xs-env` 对齐 `emu` / `NEMU` 路径
  - 不再默认 `--no-diff`

### 真实 interrupt 路径

新增/修改：

- [runtime/arch/riscv64/trap.S](/home/dfpmts/XS/framework/snippetgen-demo/runtime/arch/riscv64/trap.S)
  - 实现真实 trap entry
  - 当前采用 `mscratch` + machine timer one-shot fast path
- [runtime/src/xsrt_intr.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_intr.c)
  - 真实设置 `mtvec/mscratch/mie/mstatus`
  - 真实写 `mtimecmp`
- [runtime/include/xsrt_intr.h](/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsrt_intr.h)
- [runtime/include/xsrt_trap.h](/home/dfpmts/XS/framework/snippetgen-demo/runtime/include/xsrt_trap.h)
- [runtime/src/xsrt_env.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_env.c)
  - 增加 `xsrt_current_env()`
- [runtime/src/xsrt_trap.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_trap.c)

### interrupt proof suite

新增：

- [snippets/include/xs_interrupt_response.h](/home/dfpmts/XS/framework/snippetgen-demo/snippets/include/xs_interrupt_response.h)
- [snippets/interrupt/interrupt_response_wait.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/interrupt/interrupt_response_wait.c)
- [snippets/interrupt/check_interrupt_response.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/interrupt/check_interrupt_response.c)
- [snippets/manifests/interrupt_response_wait.yaml](/home/dfpmts/XS/framework/snippetgen-demo/snippets/manifests/interrupt_response_wait.yaml)
- [snippets/manifests/check_interrupt_response.yaml](/home/dfpmts/XS/framework/snippetgen-demo/snippets/manifests/check_interrupt_response.yaml)
- [suites/interrupt_response_poc.yaml](/home/dfpmts/XS/framework/snippetgen-demo/suites/interrupt_response_poc.yaml)

修改：

- [snippets/scalar_load_legality/arm_timer.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/arm_timer.c)

### `vsetvl` search suite

新增：

- [snippets/vector_interrupt/vsetvl_interrupt_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/vector_interrupt/vsetvl_interrupt_search.c)
- [snippets/vector_interrupt/check_vsetvl_interrupt_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/vector_interrupt/check_vsetvl_interrupt_search.c)
- [snippets/manifests/vsetvl_interrupt_search.yaml](/home/dfpmts/XS/framework/snippetgen-demo/snippets/manifests/vsetvl_interrupt_search.yaml)
- [snippets/manifests/check_vsetvl_interrupt_search.yaml](/home/dfpmts/XS/framework/snippetgen-demo/snippets/manifests/check_vsetvl_interrupt_search.yaml)
- [suites/vsetvl_interrupt_search_poc.yaml](/home/dfpmts/XS/framework/snippetgen-demo/suites/vsetvl_interrupt_search_poc.yaml)

### 测试与 runner 结果分类

修改：

- [tests/test_snippet_loading.py](/home/dfpmts/XS/framework/snippetgen-demo/tests/test_snippet_loading.py)
- [tests/test_build_pipeline.py](/home/dfpmts/XS/framework/snippetgen-demo/tests/test_build_pipeline.py)
- [tests/test_run_pipeline.py](/home/dfpmts/XS/framework/snippetgen-demo/tests/test_run_pipeline.py)
- [targets/xiangshan-verilator/run_target.py](/home/dfpmts/XS/framework/snippetgen-demo/targets/xiangshan-verilator/run_target.py)

补充了：

- interrupt proof suite 的 build/load/ELF 级测试
- `bad trap` 分类测试
- `vsetvl` search suite 的源级约束测试

## 本次运行结果摘要

### interrupt proof

- suite: `interrupt_response_poc`
- 结果：`HIT GOOD TRAP`
- 说明：真实 timer interrupt 已进入处理器并被软件环境观察到

### baseline `vsetvl`

- suite: `vsetvl_interrupt_path_poc`
- 结果：`HIT GOOD TRAP`
- 说明：基础 `vsetvl` 路径在真实 interrupt 下仍然正常结束

### search `vsetvl`

#### 旧版 search 模型

- 早期搜索版在更大运行预算下主要表现为：
  - `HIT BAD TRAP`
  - 某些 seed 接近 timeout

#### 当前 one-shot timer + dense `vsetvl` 模型

- `seed = 0x1234`
  - 结果：XiangsShan 内部断言
  - 断言点：`Rob.sv:87867`
  - 含义：`deqPtr is older than enqPtr!`

- `seed = 0xffff`
  - 结果：`timeout after 180s`
  - stdout 为空
  - 当前是最值得进一步抓波形的候选

## 这轮调查里踩过的坑

1. 不要把“程序最终 `good trap`”误当成“真实 interrupt 已响应”
   - 必须要有 trap cause / trap epc / interrupt_count 这类证据

2. 不要把“纯 interrupt 打进 `vsetvl`”误当成已经复现文档机制
   - 文档强调的是混合 `flushAfter + flushSelf`

3. 不要把 test runner 和真实 `run` 并行跑到同一个 suite build 目录
   - 测试 `setUp()` 会清理 `build/`
   - 这会制造假的 `stdout/stderr missing`

4. 不要只看 `timeout`
   - 有些 timeout 只是 host-time 边界
   - 要结合更大预算、单独运行结果、stdout/stderr 内容一起判断

## 当前最准确的阶段性判断

截至这份记录：

- 真实 interrupt 响应已经证实
- search 版 `vsetvl` workload 已经足以触发：
  - 主 ROB 指针不变量断言
  - `bad trap`
  - 某些 seed 的长时间超时
- 但还不能严谨地声称“已经确认复现微结构卡死”

当前最值得继续追的对象是：

- `seed = 0x1234`
  - 因为它已经直接命中与文档一致的 ROB 指针异常
- `seed = 0xffff`
  - 因为它在当前 one-shot timer + dense `vsetvl` 模型下表现为长时间超时

## 建议的下一步

1. 对 `seed = 0x1234` 抓 assertion 前后的波形
   - 目标：确认它与文档中的 mixed redirect / pointer bookkeeping 是否一致

2. 对 `seed = 0xffff` 用 `-b/-e/--dump-wave` 重跑
   - 目标：确认它是否接近真实 hang，而不是单纯长时间运行

3. 如果需要继续做 seed 搜索，优先保留当前模型：
   - 单次小 timer arm
   - 大量 `vsetvl zero, zero, zero`
   - 不要回退到“每轮重 arm”的模型
