# 2026-04-13 `prefetch.w` / `M_PFW` / difftest 调查笔记

## 目标

这轮调查聚焦两个问题：

1. XiangShan 上 `prefetch.w` 的真实请求流是什么，尤其是 `LoadUnit/HybridUnit -> DCache -> MissQueue` 上的 `M_PFW` 行为。
2. 旧运行日志里的这条报错究竟来自哪里：

```text
ERROR: invalid mem write to paddr 0x6950596752210f3e, NEMU raise access exception
```

特别要确认它是不是：

- `LoadEvent/StoreEvent` checker 本身打出来的
- `DiffRefillEvent` / `goldenmem` / `ref_memcpy` 之类的旁路同步逻辑间接打出来的
- 还是 NEMU 自己在执行架构内存写路径时打出来的

## 调查对象

仓库内相关 suite / snippet：

- [suites/prefetchw_tl_denied_fault_poc.yaml](../suites/prefetchw_tl_denied_fault_poc.yaml)
- [snippets/cbo/prefetchw_tl_denied_fault.c](../snippets/cbo/prefetchw_tl_denied_fault.c)
- [snippets/cbo/check_prefetchw_tl_denied_fault.c](../snippets/cbo/check_prefetchw_tl_denied_fault.c)
- [snippets/include/xs_prefetchw.h](../snippets/include/xs_prefetchw.h)

历史运行产物：

- `build/prefetchw_no_trap_poc/runs/prefetchw_try_4660/seed_4660/`
- `build/prefetchw_tl_denied_fault_poc/runs/pfprobe4660/seed_4660/`

外部代码树：

- `/home/dfpmts/XS/xs-env/XiangShan`
- `/home/dfpmts/XS/xs-env/NEMU`

## 关键结论

### 1. `prefetch.w` 在 XiangShan 中确实走 `M_PFW` DCache miss 流

`prefetch.w` 并不是在 XiangShan 里被完全吞掉的 hint。

在当前实现中：

- `LoadUnit` 会把 software `prefetch.w` 作为 DCache 请求发出，`cmd = M_PFW`
  - [LoadUnit.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/mem/pipeline/LoadUnit.scala#L403)
- `HybridUnit` 也有同样的 `M_PFW` 路径
  - [HybridUnit.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/mem/pipeline/HybridUnit.scala#L283)
- `LoadPipe` 明确接受 `M_PFW`
  - [LoadPipe.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/dcache/loadpipe/LoadPipe.scala#L147)
- `M_PFW` 在 cache 常量里被视为 `isPrefetch(cmd)`，同时又被视为 `isWriteIntent(cmd)`
  - [CacheConstants.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/CacheConstants.scala#L31)
  - [CacheConstants.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/CacheConstants.scala#L63)

因此，`prefetch.w` 在 XiangShan 里具备两层语义：

- 前端 / 架构意图上是 software prefetch
- cache 权限和 miss 行为上又带有 write-intent

### 2. `late tl_denied -> LoadAccessFault` 这条路径是存在的

当前 XiangShan 代码允许 `prefetch.w` 经过如下路径：

1. 首次 miss 进入 `MissQueue`
2. TL `denied/corrupt` 被记录进 refill error
3. error meta 被写入 DCache line
4. 后续命中同一 line 时，`LoadPipe` 读出 delayed `tl_denied`
5. `LoadUnit` s3 再把它并回 `loadAccessFault`

对应证据：

- `MissQueue` 记录 refill error
  - [MissQueue.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/dcache/mainpipe/MissQueue.scala#L917)
- `LoadPipe` 从 extra meta 读出 hit error / delayed TL error
  - [LoadPipe.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/dcache/loadpipe/LoadPipe.scala#L284)
  - [LoadPipe.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/dcache/loadpipe/LoadPipe.scala#L320)
  - [LoadPipe.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/cache/dcache/loadpipe/LoadPipe.scala#L557)
- `LoadUnit` 注释中先说 software prefetch 不应触发异常，但 s3 仍并回 delayed fault
  - [LoadUnit.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/mem/pipeline/LoadUnit.scala#L1221)
  - [LoadUnit.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/mem/pipeline/LoadUnit.scala#L1624)

这也是当前 `prefetchw_tl_denied_fault_poc` 被设计成 probe 型而不是硬性 pass/fail reproducer 的原因。

### 3. 旧日志里的 `invalid mem write` 不是 `LoadEvent/StoreEvent` checker 打出来的

这条报错来自 NEMU 自己的 `paddr_write()`：

- [paddr.c](../../../xs-env/NEMU/src/memory/paddr.c#L375)
- 具体打印点在 [paddr.c](../../../xs-env/NEMU/src/memory/paddr.c#L426)

旧日志内容见：

- `build/prefetchw_no_trap_poc/runs/prefetchw_try_4660/seed_4660/stdout.log`

其中关键片段为：

```text
ERROR: invalid mem write to paddr 0x6950596752210f3e, NEMU raise access exception
[src/memory/paddr.c:218,check_paddr] isa pmp check failed
Core 0 dump: HIT CRITICAL ERROR: please check if software cause a double trap.
Core 0: HIT GOOD TRAP at pc = 0x800006cc
```

这说明：

- `invalid mem write` 是 NEMU 真正走到了一个写物理地址的路径
- 不是 difftest C++ 里某个 compare-only checker 自己打印的字符串

### 4. `RefillChecker` / `ref_memcpy` / `goldenmem` 不是这条 `invalid mem write` 的来源

原因分三层：

1. `RefillChecker` 的同步动作是 `proxy->ref_memcpy(...)`
   - [refill.cpp](../../../xs-env/XiangShan/difftest/src/test/csrc/difftest/checkers/refill.cpp#L64)
2. `load.cpp` 里的某些恢复路径也调用 `proxy->ref_memcpy(...)`
   - [load.cpp](../../../xs-env/XiangShan/difftest/src/test/csrc/difftest/checkers/load.cpp#L233)
3. 但 NEMU 的 `difftest_memcpy()` 实现只是 `guest_to_host()+memcpy()`，不走 `NEMU/src/memory/paddr.c`
   - [ref.c](../../../xs-env/NEMU/src/cpu/difftest/ref.c#L71)
   - [ref.c](../../../xs-env/NEMU/src/cpu/difftest/ref.c#L97)

因此：

- `ref_memcpy()` 不会触发 `paddr_write()`
- 也不会打出 `ERROR: invalid mem write ...`

另外，XiangShan difftest 自己的 `goldenmem.cpp` 里虽然也有一个本地 `paddr_write()`：

- [goldenmem.cpp](../../../xs-env/XiangShan/difftest/src/test/csrc/difftest/goldenmem.cpp#L191)

但它的失败模式是 `panic("write not in pmem!")`，不是旧日志里的 NEMU 报错字符串。

### 5. 当前 NEMU 并没有把 `prefetch.w` 当成专门的 prefetch 指令解码

这是这次调查里最重要的一点。

当前 NEMU：

- `rvcbo/decode.h` 只包含 `cbo.zero/inval/flush/clean`
  - [rvcbo/decode.h](../../../xs-env/NEMU/src/isa/riscv64/instr/rvcbo/decode.h#L16)
- 主 decode 仍会把 `0010011` 送入 `op_imm`
  - [decode.c](../../../xs-env/NEMU/src/isa/riscv64/instr/decode.c#L69)
- `op_imm` 中 `funct3 = 110` 会落到 `ori`
  - [decode.h](../../../xs-env/NEMU/src/isa/riscv64/instr/rvi/decode.h#L141)

而旧 case 中 `prefetch.w` 的机器码是：

```text
0x0037e013
```

这条机器码按通用编码拆出来就是：

- opcode = `0x13`
- rd = `x0`
- funct3 = `110`
- rs1 = `x15`
- imm = `0x3`

也就是：

```text
ori x0, x15, 3
```

所以在当前参考模型里：

- DUT 执行的是带真实 cache/miss 语义的 `prefetch.w`
- REF 执行的不是 prefetch，而是一个等价于 NOP 的 `ori`

这意味着两边在该指令处就已经语义分叉。

### 6. 旧日志里的 `HIT CRITICAL ERROR` 不是单边 REF 报错

这条日志不是 NEMU 自己直接打印的红字版本，而是 difftest `CriticalErrorChecker` 打出来的：

- [traps.cpp](../../../xs-env/XiangShan/difftest/src/test/csrc/difftest/checkers/traps.cpp#L140)

`CriticalErrorChecker` 的语义是：

- 当 `proxy->raise_critical_error()` 返回值与 DUT 的 `DiffCriticalErrorEvent` 相等时
- 打印 `HIT CRITICAL ERROR`
- 然后把状态记成 trap

而 XiangShan 侧的 critical error event 来自 CSR/Trap 逻辑：

- [NewCSR.scala](../../../xs-env/XiangShan/src/main/scala/xiangshan/backend/fu/NewCSR/NewCSR.scala#L1543)

因此旧日志说明：

- 当时 DUT 和 REF 都进入了 critical-error 对齐状态
- 不是单边 REF 自己崩了，DUT 还正常

## 旧 case 与当前 probe case 的关系

### 旧 case：`prefetchw_no_trap_poc`

旧 case 的目标是验证：

- `prefetch.w` 访问受限区域
- 不应 trap
- trap ledger 必须全零

它在一次历史运行中出现了：

- `invalid mem write`
- `isa pmp check failed`
- `HIT CRITICAL ERROR`
- 最后仍被 runner 记为 `good_trap`

这暴露了两个问题：

1. case 目标过于刚性，无法表达“当前实现可能出现 delayed `tl_denied` bug”
2. runner 分类里 `good_trap` 对 `critical_error` 的优先级不够高

### 当前 case：`prefetchw_tl_denied_fault_poc`

当前 case 已进一步简化成最小 probe：

- 对同一个 low-address 目标先做一次普通 `load`
- 再对同一地址做一次 `prefetch.w`
- 安装 trap handler 记录最后一次 trap 的 `phase/cause/tval/epc`
- checker 允许两种结果都通过：
  - 没有 trap
  - 出现 `mcause = 5` 的 `LoadAccessFault`

当前仓库默认目标地址已经改成 `0x20000000`。在当前默认 `SimMMIO` 地址图下：

- `0x10000000..0x1fffffff` 是 flash 窗口
- `0x20000000` 不在已知 flash / UART / on-chip peripheral / SD / intrGen 窗口内

因此它比 `0x10000000` 更接近“明确 low-2GB hole”。

当前仓库中对应文件：

- [suites/prefetchw_tl_denied_fault_poc.yaml](../suites/prefetchw_tl_denied_fault_poc.yaml)
- [snippets/cbo/prefetchw_tl_denied_fault.c](../snippets/cbo/prefetchw_tl_denied_fault.c)
- [snippets/cbo/check_prefetchw_tl_denied_fault.c](../snippets/cbo/check_prefetchw_tl_denied_fault.c)

当前环境下的一次实际运行：

- `build/prefetchw_tl_denied_fault_poc/runs/pfprobe4660/seed_4660/stdout.log`

表现为正常 `HIT GOOD TRAP`，没有复现旧的 `invalid mem write`。

## 已排除项

截至本笔记，可以明确排除这些解释：

### 1. 不是显式 `LoadEvent/StoreEvent` checker 直接打印

`invalid mem write` 字符串并不在这些 checker 中。

### 2. 不是 `RefillChecker` 通过 `ref_memcpy` 间接触发

`ref_memcpy` 在 NEMU 里不经过 `paddr_write()`。

### 3. 不是 XiangShan difftest `goldenmem` 的本地报错

`goldenmem.cpp` 的错误模式和日志字符串不匹配。

### 4. 不是当前 `prefetchw_tl_denied_fault_poc` 运行中的现象

当前 probe suite 的实际运行日志没有出现这条报错。

## 目前最合理的解释

当前最符合证据链的解释是：

1. DUT 将 `prefetch.w` 当成真实 `M_PFW` 请求执行，并可能经过 `late tl_denied` 路径。
2. REF 没有实现 `prefetch.w` 的专门 decode，而是把对应机器码当成 `ori x0, rs1, imm`。
3. 两边从这条指令开始语义分叉。
4. 后续执行流跑偏后，REF 在某个普通写内存路径上调用了 `paddr_write()`。
5. 由于地址已经偏到异常值，NEMU 打出：

```text
ERROR: invalid mem write to paddr ...
```

6. 随后 DUT/REF 在 trap/critical-error 状态上又重新对齐，于是 `CriticalErrorChecker` 打出 `HIT CRITICAL ERROR`。

## 还没有完全闭合的问题

虽然现在已经能判断 `invalid mem write` 来自 NEMU 自己的架构写路径，但还没完全闭合这一点：

> 究竟是哪一条 NEMU 指令、在什么 PC 上，触发了那次 `paddr_write()`？

也就是说，现在已经知道：

- 不是 difftest compare/sync helper
- 不是 refill/globalmem checker
- 是 REF 的真实写路径

但还不知道：

- 那条写是哪个具体指令执行出来的
- 它和 `prefetch.w` 的语义分叉之间隔了多少条指令
- 是否存在一条稳定的“跑偏后 store”链路

## 最值得继续做的下一步

如果继续深挖，优先级最高的是直接在 NEMU 写路径打诊断：

1. 在 [paddr.c](../../../xs-env/NEMU/src/memory/paddr.c#L426) 附近临时打印：
   - `cpu.pc`
   - `vaddr`
   - `addr`
   - `cpu.mode`
2. 必要时打印最近一次 store commit 相关 PC
3. 再用历史 case 或等价复现重新跑一次

这样可以直接回答：

- 哪条 REF 指令发起了这次非法写
- 它是否就是 `prefetch.w` 被错误解码后的连锁后果

第二优先级才是：

- 给 NEMU 补 `prefetch_w/prefetch_r/prefetch_i` 的真正 decode/execute 语义
- 或者在 `run_target` 里提高 `critical_error` / `invalid mem write` 的失败优先级

## 一句话总结

截至目前，`prefetch.w` 在 XiangShan DUT 中确实形成了 `M_PFW` miss/refill/error-meta 路径；旧日志里的 `invalid mem write` 则确认来自 NEMU 自己的 `paddr_write()`，而不是 difftest 的 refill/globalmem/checker 旁路逻辑。当前最强的根因怀疑是：REF 根本没有把 `prefetch.w` 当作 prefetch 解码，导致 DUT/REF 从该指令开始语义分叉，随后 REF 在跑偏执行中触发了一次真实非法写。
