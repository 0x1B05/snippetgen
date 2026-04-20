# Deferred Check Suite Design

**Date:** 2026-04-20

**Goal**

让 `snippetgen-demo` 支持“多个 snippets 组合跑完以后再统一 check”，避免单个 snippet 的即时 `.check` 干扰跨-snippet 组合验证。

**Non-Goal**

- 不改变现有 suite 的行为
- 不要求所有 snippet 都重写成无 `.check` 风格
- 不在这一轮引入复杂的 phase DAG 或多轮交错执行模型

## 1. 当前行为与问题

当前 runtime 的执行语义固定为：

- `init`
- `run`
- `check`
- `fini`

实现见：

- [xsrt_snippet.c](/home/dfpmts/XS/framework/snippetgen-demo/runtime/src/xsrt_snippet.c)

当前 harness 逐个 snippet 调用 `xsrt_run_snippet()`：

- [emitter.py](/home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/emitter.py)

这意味着：

1. 只要 snippet 自己定义了 `.check`，它一定会在自己的 `run` 之后立刻执行
2. 如果一个 suite 需要组合多个 snippet 的运行结果再做总验证，当前唯一稳定做法是：
   - 业务 snippets 不写 `.check`
   - 最后额外放一个独立 check snippet

这对“框架允许 snippet 保留自己的 `.check` 能力，但 suite 选择延迟 check”这个需求还不够。

## 2. 需求澄清

目标不是“完全禁用 snippet 的 `.check`”，而是：

- snippet 仍然可以带 `.check`
- suite 可以声明：先把一组 snippets 全部 `run` 完
- 然后再统一执行 check 阶段

这样可以避免：

- 某个中间 snippet 的 `.check` 在组合尚未完成时提前失败
- 中间 `.check` 读到尚未准备好的共享状态
- 为了避免上述问题，被迫把所有 check 都拆到额外文件里

## 3. 方案选择

### 方案 A：只靠约定，不改框架

做法：

- 继续要求“业务 snippets 不写 `.check`”
- 总验证永远写成末尾独立 check snippet

优点：

- 零框架改动
- 现有 suite 已经兼容

缺点：

- 不满足“snippet 本身可以有 `.check`，但 suite 可以延迟执行”的新需求
- 约定容易漂移，框架没有第一性支持

### 方案 B：在 snippet manifest 里加 `check_policy`

做法：

- manifest 增加 `check_policy: immediate|deferred|never`

优点：

- snippet 粒度最灵活

缺点：

- 行为分散，不容易从 suite 一眼看出执行顺序
- 同一个 snippet 被多个 suite 复用时，策略可能不一致
- 配置面过细，复杂度高于当前需求

### 方案 C：suite 显式分成 `run_snippets` 和 `check_snippets`

做法：

- 让 suite 自己声明运行阶段和检查阶段
- 运行 snippets 先统一 `run`
- 检查 snippets 后统一 `check`

优点：

- suite 级语义最清晰
- 兼容现有组合型 workload 的直觉
- 能直接表达“多个 snippets 跑完后一起 check”
- 未来如需更复杂 phase，还能在 suite 层继续扩展

缺点：

- 需要调整 suite schema 和 harness 生成

**推荐：方案 C**

原因：

- 需求本质上是 suite 级编排，而不是 snippet 元数据本身的问题
- 让 suite 显式表达 phase，比让每个 snippet 自己带策略更清晰
- 对现有老 suite 的兼容也最好做

## 4. 最终设计

### 4.1 Suite Schema

保留现有 schema：

```yaml
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - some_snippet
    - finish_check
```

新增一套显式 phase schema：

```yaml
compose:
  mode: sequence
  run_snippets:
    - init_basic_env
    - snippet_a
    - snippet_b
  check_snippets:
    - snippet_a
    - snippet_b
    - finish_check
```

约束：

- `compose.snippets` 与 `compose.run_snippets/check_snippets` 二选一
- 不能混用
- `check_snippets` 不能为空
- `run_snippets` 不能为空

语义：

- `run_snippets` 只执行 `init -> run -> fini`
- `check_snippets` 只执行 `check`

这允许两种用法：

1. 统一末尾检查：
   - `run_snippets: [a, b, c]`
   - `check_snippets: [check_final, finish_check]`
2. 延迟执行已有 snippet 的 `.check`：
   - `run_snippets: [a, b]`
   - `check_snippets: [a, b, finish_check]`

第二种模式就是新需求要的核心能力。

### 4.2 Runtime Helper

当前只有：

- `xsrt_run_snippet()`

新增两个 helper：

```c
int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
```

语义分别为：

- `xsrt_run_snippet_no_check()`
  - 执行 `init`
  - 执行 `run`
  - 不执行 `check`
  - 执行 `fini`

- `xsrt_run_snippet_check_only()`
  - 不执行 `init`
  - 不执行 `run`
  - 只执行 `check`
  - 不执行 `fini`

不修改现有 `xsrt_run_snippet()`，它继续保持原语义。

### 4.3 `fini` 策略

`fini` 仍然跟在运行阶段后立即执行，不延迟。

原因：

1. 当前仓库里几乎没有依赖“延迟 `fini`”的 snippet
2. 已存在的 `.fini` 例子，比如 [prefetchw_tl_denied_fault.c](/home/dfpmts/XS/framework/snippetgen-demo/snippets/cbo/prefetchw_tl_denied_fault.c)，本质上是在 run 后卸 trap，适合立即清理
3. 真正需要跨-snippet 留给最终 check 的状态，应该落在：
   - `env->flags`
   - `env->snippet_id`
   - debug CSR
   - 共享静态内存

而不是依赖 `fini` 之后仍保持某些临时执行环境。

因此，新的 phase 设计不会引入“run 完但不 fini”的半闭合状态。

### 4.4 Harness 生成

对于旧 schema：

```c
rc = xsrt_run_snippet(&env, &snippet_x);
```

保持不变。

对于新 schema，harness 分两段：

```c
rc = xsrt_run_snippet_no_check(&env, &snippet_a);
if (rc != 0) { ... }

rc = xsrt_run_snippet_no_check(&env, &snippet_b);
if (rc != 0) { ... }

rc = xsrt_run_snippet_check_only(&env, &snippet_a);
if (rc != 0) { ... }

rc = xsrt_run_snippet_check_only(&env, &snippet_b);
if (rc != 0) { ... }
```

最后仍由 harness 统一：

- `xsrt_finish_fail(&env, rc)`
- 或 `xsrt_finish_pass(&env)`

### 4.5 数据模型

当前 `SuiteSpec` / `ComposePlan` 只有一份 `snippet_ids`。

需要扩展为：

```python
@dataclass(frozen=True)
class SuiteSpec:
    ...
    compose_mode: str
    snippet_ids: tuple[str, ...]
    run_snippet_ids: tuple[str, ...] | None = None
    check_snippet_ids: tuple[str, ...] | None = None
```

`ComposePlan` 同理。

约定：

- 旧 schema 时：
  - `snippet_ids` 保持现有意义
  - `run_snippet_ids` / `check_snippet_ids` 为 `None`
- 新 schema 时：
  - `snippet_ids` 作为去重后的“全集”
  - `run_snippet_ids` / `check_snippet_ids` 保存 phase 顺序

这样：

- 老调用点尽量不坏
- emitter 可以基于 phase 信息做不同分支

## 5. 兼容策略

### 5.1 对现有 suite 的兼容

所有现有 suite 继续使用：

- `compose.snippets`

且语义完全不变。

这意味着当前大量 build/run tests 不需要整体改写，只需补新分支测试。

### 5.2 对现有 snippet 的兼容

现有 snippet descriptor 结构不变：

- [xs_snippet.h](/home/dfpmts/XS/framework/snippetgen-demo/snippets/include/xs_snippet.h)

不要求任何 snippet 立刻改 manifest。

只是在新 suite 里，框架可以选择：

- 让它即时 `check`
- 或延迟到 suite 的 `check_snippets` 阶段再跑

## 6. 适用场景

### 6.1 适合使用延迟 check 的 suite

- 多个 run snippet 共享同一块 arena/CSR/env 状态
- 中间 run snippet 只负责制造现场
- 最终 check 要看组合结果
- 一个 snippet 的 `.check` 依赖别的 snippet 先完成

### 6.2 不适合使用延迟 check 的 suite

- snippet 本身是自洽的小闭环
- check 只是立即验证本 snippet 的 run 输出
- `run` 完之后不需要其他 snippet 再改变上下文

这种情况下继续用老的 `compose.snippets` 即可。

## 7. 测试策略

### 7.1 Suite Loader Tests

新增测试覆盖：

- 新 schema 能解析
- 新旧 schema 不能混用
- 缺少 `run_snippets` 或 `check_snippets` 时报错
- deterministic plan 正确保留 phase 顺序

### 7.2 Runtime Surface Tests

新增测试覆盖：

- `xsrt_run_snippet_no_check()`
  - 执行 `init/run/fini`
  - 不执行 `check`
- `xsrt_run_snippet_check_only()`
  - 只执行 `check`

### 7.3 Build Pipeline Tests

新增测试覆盖：

- 新 schema 生成的 harness 确实分成 run/check 两段
- 同一 snippet 出现在 `run_snippets` 和 `check_snippets` 中时，只生成一个 descriptor 声明/包装，但在 main 里调用两次不同 helper

### 7.4 New Integration Suite

增加一个最小集成 suite，专门验证新能力：

- `snippet_mark_stage_a`
  - `run` 写 `env->flags`
  - `check` 需要看到 `snippet_mark_stage_b` 的结果才能通过
- `snippet_mark_stage_b`
  - `run` 再补充状态
  - `check` 验证完整组合

这个 suite 用新 schema：

```yaml
compose:
  mode: sequence
  run_snippets:
    - snippet_mark_stage_a
    - snippet_mark_stage_b
  check_snippets:
    - snippet_mark_stage_a
    - snippet_mark_stage_b
    - finish_check
```

如果框架仍旧按老语义即时 `check`，它会失败；只有真正实现延迟 check 才会通过。

## 8. 风险与对策

### 8.1 风险：重复执行同一 snippet 的副作用

对策：

- `check_only` 明确不跑 `init/run/fini`
- phase 之间只允许重复执行 `.check`

### 8.2 风险：`fini` 太早执行导致 check 看不到状态

对策：

- 明确规定跨-snippet 检查状态必须放在 `env` / CSR / 共享内存
- 不支持依赖 `fini` 延迟的隐藏状态

### 8.3 风险：suite schema 变复杂

对策：

- 旧 schema 保持最简单路径
- 新 schema 只增加一层 phase，不引入任意 DAG

### 8.4 风险：同一 snippet 多次引用导致 emitter 重复声明

对策：

- 保持当前 emitter 的 descriptor 去重逻辑
- 只在 main 中重复发起 phase-specific 调用

## 9. 推荐推进顺序

1. 先做 loader/model/runtime/emitter 的最小支持
2. 再加一个专门的 integration suite 证明延迟 check 生效
3. 最后才把现有 scalar misalign 或其他组合型 suite 迁移到新 schema

## 10. 验收标准

- 现有 `compose.snippets` suite 行为完全不变
- 新 suite schema 支持 `run_snippets` + `check_snippets`
- 框架支持同一 snippet 在 run 阶段和 check 阶段分别参与
- `fini` 仍在 run 阶段立即执行
- 至少一个新的 integration suite 证明“多个 snippets 先组合运行，再统一 check”确实生效
