# Scalar Misalign Snippet Matrix Design

**Date:** 2026-04-20

**Goal**

基于 `/home/dfpmts/XS/kmh-v2/docs/scalar-misalign-validation-points-2026-04-16.md`，在 `snippetgen-demo` 里建立一套分阶段推进的 scalar misalign 验证 snippets，并在 XiangShan `emu` 上做真实运行闭环。

**Non-Goal**

- 不覆盖 vector misalign 主流程
- 不试图直接证明硬件内部 signal 是否“进入某个 buffer”或“只发出一次 wakeup”
- 不在这一轮引入新的 runner 或波形自动分析框架

## 1. 背景和约束

`kmh-v2` 文档列出的验证点同时包含两类内容：

1. 可以被软件直接观测的最终语义
   - 读写结果是否正确
   - 是否 trap，以及 trap 类型是否正确
   - `mtval/tval` 是否指向 faulting half
   - younger load 是否读到了 older misalign store 的完整值
2. 只能通过硬件内部状态证明的实现细节
   - 是否进入 `LoadMisalignBuffer` / `StoreMisalignBuffer`
   - `curPtr/unSentLoads` 是否按模板变化
   - 是否只有一次 wakeup/writeback
   - owner / revoke / sq bookkeeping 的内部仲裁

`snippetgen-demo` 当前最适合承载第一类。第二类只能通过软件代理语义间接验证，不能把内部状态当成直接断言目标。

因此本设计采用分阶段路线：

- Phase 1：做固定语义 smoke，用最小代价把基础 split/misalign 读写和 trap 路径跑起来
- Phase 2：扩展到中等矩阵，用 `proc + check` 结构把模板覆盖和 cross-page/permission 类问题补齐
- Phase 3：补 seed 驱动的搜索型 probe，针对 forwarding/replay/older-store 竞争等角落

## 2. 方案选择

### 方案 A：全部做成 AM `main()` 程序

优点：

- 与当前 `nexus-am` 迁移路径一致
- 返回码和 trap 语义闭环简单
- 实际 `emu` 运行最稳定

缺点：

- 不适合做大量组合矩阵
- 调试信息难复用
- 对 phase 2/3 的搜索型 probe 支撑不足

### 方案 B：全部做成 `proc + check` 结构

优点：

- 与现有 [unaligned_load.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/unaligned_load.c) 和 [misaligned_split_store_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/store_forward/misaligned_split_store_search.c) 一致
- 可以用 `env->flags`、`env->snippet_id` 和 debug CSR 保留现场
- 便于扩展成模板矩阵和 seed 搜索

缺点：

- 第一批 smoke case 实现会比 AM `main()` 更重
- trap handler / debug 约定要先定义

### 方案 C：混合方案，按阶段切换

优点：

- Phase 1 用 AM `main()` 快速闭环
- Phase 2/3 切到 `proc + check`，沿用现有 snippet 风格
- 能兼顾稳定性、覆盖面和调试性

缺点：

- 框架形态有两种，需要提前定义好切换边界

**推荐：方案 C**

原因是它最符合当前仓库状态。Phase 1 先用最少代码证明 `emu` 上的 scalar misalign 基础语义；等 smoke 闭环后，再把中等矩阵和搜索型 probe 建到 `proc + check` 路径上。

## 3. 总体架构

### 3.1 Phase 1：最小 smoke 集合

Phase 1 产出 4 到 6 个 `am_program` 风格用例，每个用例只验证一个软件可观测点。

推荐的首批集合：

1. `scalar_misalign_load_in_16b_main`
   - 验证文档 `L1`
   - 同 16B 内 misalign `LW/LD` 读值正确且不 trap
2. `scalar_misalign_load_cross_16b_main`
   - 验证 `L2/L6` 的最小软件语义
   - 跨 16B `LD` split 后合并结果正确
3. `scalar_misalign_store_in_16b_main`
   - 验证 `S1`
   - 同 16B 内 misalign `SW/SD` 写入后字节结果正确
4. `scalar_misalign_store_cross_16b_main`
   - 验证 `S4`
   - 跨 16B `SD` 后两侧字节片段正确落地
5. `scalar_misalign_store_load_overlap_main`
   - 验证 `L9` 的最小软件代理语义
   - older misalign store 之后的 younger load 必须读到完整值，而不是半条结果

Phase 1 只要求：

- build 成功
- `emu` 实际运行完成
- 每个 suite 都有明确 pass/fail

Phase 1 不尝试证明 replay、owner、wakeup 次数等内部实现细节。

### 3.2 Phase 2：中等验证矩阵

Phase 2 统一切换到 `proc + check` 结构。每个“执行 snippet”负责发出访存与记录现场；每个“check snippet”负责解释 `env` 和 debug CSR 中的结果。

Phase 2 的矩阵分为 4 组：

1. load split 模板组
   - `LW 3+1`
   - `LW 2+2`
   - `LW 1+3`
   - `LD 7+1`
   - `LD 4+4`
   - `LD 1+7`
2. store split 模板组
   - `SW 3+1`
   - `SW 2+2`
   - `SW 1+3`
   - `SD 7+1`
   - `SD 4+4`
   - `SD 1+7`
3. cross-page / permission 组
   - load：第一页正常、第二页 page fault
   - load：第一页正常、第二页 access fault
   - store：第一页正常、第二页 page fault
   - store：第一页正常、第二页 access fault
4. overlap / forwarding 组
   - older misalign store 完整后，younger load 可见完整值
   - older misalign store 尚未构成完整可见结果时，younger load 不得读到半条拼接值

这一阶段不强求把每一种 split 模板都拆成一个独立 suite。可以按“一个 suite 多个 snippet”的方式，把同类模板收敛到少量 suite 里。

### 3.3 Phase 3：搜索型 probe

Phase 3 面向文档中更偏微结构交互的风险点，只做少量 seed 驱动 probe，不承诺一次性穷尽。

建议的首批 probe：

1. `scalar_misalign_store_forward_search`
   - 延续当前 [misaligned_split_store_search.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/store_forward/misaligned_split_store_search.c) 思路
   - 强化 older misalign store / younger load overlap 探测
2. `scalar_misalign_cross_page_fault_search`
   - 搜索不同页边界、不同偏移下的 trap 地址与 fault 类型归属
3. `scalar_misalign_replay_probe`
   - 通过 cacheline 切换、地址混洗和重复访问，探测“出现 replay 时仍能收口”的软件代理语义

Phase 3 的结果允许是两类：

- 严格 pass/fail suite
- probe 型 suite：不要求一定复现 bug，但必须稳定导出足够调试信息

## 4. 软件可观测代理语义

由于不少验证点本身是内部实现语义，本设计把它们映射成软件可检查代理：

### 4.1 `不进入 misalign buffer`

不能直接观察。改成验证：

- 同 16B misalign 不 trap
- 最终 load/store 结果正确
- 不需要额外 trap handler / replay 补偿即可完成

这对应 `L1`、`S1`。

### 4.2 `split 模板正确`

不能直接读 `splitLoadReq/splitStoreReq`。改成验证：

- 不同偏移模板下的最终字节布局正确
- 合并后的寄存器结果正确
- 对 cross-page/fault 情况，trap 地址落在 faulting half

这对应 `L2`、`S4`、`L8` 以及 store 侧对应的 cross-page / permission 验证点。

### 4.3 `只发生一次最终 writeback/wakeup`

不能直接数 wakeup。改成验证：

- 最终结果只由一次软件可见收口决定
- 中间过程不会让 younger load 读到半成品数据
- check 侧看到的 completed 标志和最终结果一致

这对应 `L6`。

### 4.4 `replay 后收口正确`

不能直接断言某拍 replay。改成验证：

- 在制造 cacheline 切换、交织访问或 cross-page 情况后
- 最终结果仍然正确，且没有提前写回错误值

这对应 `L3`、`S5`。

### 4.5 `owner / revoke / oldest gating`

不能直接看仲裁。改成验证：

- 更年轻的 misalign store 不得破坏更老 store 的最终可见顺序
- redirect/restart 后不留下脏状态导致后续 case 错误

这对应 `S2`、`S3`。

## 5. 文件与命名设计

### 5.1 Phase 1

新增目录：

- `snippets/programs/`
  - `scalar_misalign_load_in_16b_main.c`
  - `scalar_misalign_load_cross_16b_main.c`
  - `scalar_misalign_store_in_16b_main.c`
  - `scalar_misalign_store_cross_16b_main.c`
  - `scalar_misalign_store_load_overlap_main.c`
- `snippets/manifests/`
  - 对应 5 个 manifest
- `suites/`
  - 对应 5 个 `*_poc.yaml`

命名原则：

- `scalar_misalign_<topic>_main` 只用于 Phase 1 的 AM 程序
- 所有 suite 统一用 `*_poc.yaml`

### 5.2 Phase 2 / 3

新增目录：

- `snippets/scalar_misalign/`
  - `load_split_templates.c`
  - `check_load_split_templates.c`
  - `store_split_templates.c`
  - `check_store_split_templates.c`
  - `cross_page_faults.c`
  - `check_cross_page_faults.c`
  - `store_forward_overlap.c`
  - `check_store_forward_overlap.c`
  - `replay_probe.c`
  - `check_replay_probe.c`
- `snippets/include/`
  - `xs_scalar_misalign.h`

`xs_scalar_misalign.h` 负责统一：

- debug CSR 编号
- flag bit 定义
- fail code
- trap cause 常量

这样 Phase 2 / 3 可以共用一套状态报告协议，而不是每个 snippet 自己随意占 CSR。

## 6. 运行与验证策略

### 6.1 每个阶段都必须有真实 `emu` 运行

不能只停在 build 和本地 unittest。

每个阶段至少要选出一组 suite，在真实 `emu` 上执行并保留：

- `stdout.log`
- `stderr.log`
- `run_meta.json`
- `batch_meta.json`

### 6.2 Phase 1 的真实运行要求

Phase 1 的 5 个 smoke suite 都必须在 `emu` 上实际运行一次。

预期结果：

- 全部 `good_trap`
- `run_meta.json` 中 `status == "ran"`
- `finish_code == 0`

### 6.3 Phase 2 的真实运行要求

Phase 2 至少选择 3 组 suite 跑实机：

- 一组 load split
- 一组 store split
- 一组 cross-page/permission

### 6.4 Phase 3 的真实运行要求

Phase 3 至少选择 1 个 probe suite 跑实机。

若是严格 pass/fail 型：

- 要求 `good_trap`

若是 probe 型：

- 可以允许 `bad_trap`，但必须有稳定、可解释的 `finish_code` 和 debug 现场

## 7. 测试策略

### 7.1 静态存在性测试

更新：

- `tests/test_snippet_loading.py`

确保新增源文件、manifest 和 suite 被索引到。

### 7.2 构建测试

更新：

- `tests/test_build_pipeline.py`

确保每个阶段至少一个代表 suite 可以 build 出：

- `generated_suite.c`
- `test.elf`
- `test.bin`
- `disasm`
- `build_manifest.json`

### 7.3 内容测试

更新：

- `tests/test_am_program_snippet_build.py`

用于 Phase 1，检查关键访存模式、trap handler、cross-page 页表布局或 overlap 路径是否存在。

Phase 2/3 如有必要，增加：

- `tests/test_scalar_misalign_matrix.py`

用于检查统一 header、debug CSR 协议和矩阵型 suite 组织是否符合预期。

### 7.4 真实运行测试

继续沿用：

- `python3 generator/cli.py run suites/<suite>.yaml --seed <seed> --batch-id <id>`

并把实际 `emu` 运行结果记入开发文档或 checkpoint。

## 8. 风险与对策

### 8.1 风险：把硬件内部语义误写成软件断言

对策：

- 所有验证点都先归类为“直接可观测”或“代理可观测”
- 计划中只实现可由软件和 trap 信息证明的断言

### 8.2 风险：cross-page fault case 先撞 PMP，而不是页表权限

对策：

- 复用当前 `nexus_memscan_page_fault_main` 和 `nexus_memscan_hugepage_access_fault_main` 已经验证过的模式
- 先配 allow-all S-mode PMP baseline，再造 page fault / access fault 差异

### 8.3 风险：probe 型 case 不稳定

对策：

- Phase 3 才引入搜索型 case
- seed 驱动 case 必须保留 debug CSR 和 `env->snippet_id`
- 不把“难稳定复现”的 case 放进 Phase 1 smoke

### 8.4 风险：suite 数量膨胀

对策：

- Phase 1 每个点单独 suite
- Phase 2 开始按组收敛，一个 suite 可以承载多个相近模板
- 只把确实需要独立 repro 的 case 单独拆 suite

## 9. 验收标准

### Phase 1

- 新增 4 到 6 个 smoke snippets
- 全部可 build
- 全部在真实 `emu` 上完成一次运行
- 结果为 `good_trap`

### Phase 2

- 新增中等矩阵 snippets/header/check suites
- 覆盖 load/store split 模板、cross-page/permission、overlap forwarding 三组
- 至少 3 组 suite 在真实 `emu` 上完成运行

### Phase 3

- 新增 2 到 3 个搜索型 probe suites
- 至少 1 个 probe 在真实 `emu` 上运行
- 若复现异常，能够通过 `finish_code` 和 debug CSR 定位

## 10. 推荐推进顺序

1. Phase 1 先拿到稳定 smoke 闭环
2. Phase 2 扩成中等矩阵
3. Phase 3 再碰搜索型 case

这样做的原因是：仓库当前已经有 misalign load/store 的最小样例和 `finish_code` 链路，应该先把“稳定可跑的最小集”做成基线，再继续向 replay/forwarding/cross-page 的复杂点推进。
