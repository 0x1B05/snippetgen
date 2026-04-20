# Scalar Misalign Family Combo Design

**Date:** 2026-04-20

**Goal**

在 `snippetgen-demo` 中为 `scalar_misalign` 家族增加一组确定性的 family-combo suites，
让现有 deterministic snippets 能以 deferred-check 方式混合运行，并在 XiangShan `emu`
上完成真实验证闭环。

**Non-Goal**

- 这一轮不把 `search/probe` snippets 混入 family combo
- 不重写现有 deterministic snippets 的核心访存逻辑
- 不引入新的 runner 或波形分析框架

## 1. 问题

现有 `scalar_misalign` deterministic snippets 已经各自能独立运行，但直接做家族内混杂会碰到共享状态覆盖：

- `load_split_templates` 和 `store_split_templates` 共用 `XS_SCALAR_MISALIGN_CSR_TEMPLATE_COUNT`
- 多个 snippets 共用 `XS_SCALAR_MISALIGN_CSR_FAIL_CASE`
- `check_load_split_templates` / `check_store_split_templates` 依赖 `env->snippet_id`

这些设计对“单 suite 单 snippet”没有问题，但对 deferred-check family combo 不够稳。
后跑的 snippet 会覆盖先跑 snippet 的 `snippet_id` 和共享 CSR，导致 check 可能出现假失败。

## 2. 方案

### 方案 A：只混当前天然不冲突的 snippets

只组合 `store_forward_overlap` 和 `cross_page_faults` 这类已经有独占 CSR 的 snippets。

优点：

- 改动最小
- 风险最低

缺点：

- 对 load/store split 家族没有实质增益
- 覆盖面太保守

### 方案 B：轻量 retrofit 现有 deterministic family snippets

给 deterministic family snippets 增加独占的 summary CSR 槽，check 只读自己的 flags 和独占 CSR，不再依赖 `env->snippet_id`。

优点：

- 改动小
- 不影响现有独立 suite 行为
- 能把 load/store split、forward、cross-page 放进同一个 family combo

缺点：

- 需要改 4 组 deterministic snippet/check

### 方案 C：新增 family-level checker

新增一个统一的 family checker，由 run snippets 只写 snapshot，最后由 family checker 统一解释。

优点：

- 最系统
- 后续最容易扩到 search/probe

缺点：

- 改动面最大
- 这一轮属于过度设计

**推荐：方案 B**

## 3. 最终设计

### 3.1 Shared-State Retrofit

在 [xs_scalar_misalign.h](/home/dfpmts/XS/framework/snippetgen-demo/snippets/include/xs_scalar_misalign.h) 中新增独占 summary CSR 槽：

- `XS_SCALAR_MISALIGN_CSR_LOAD_SPLIT_SUMMARY`
- `XS_SCALAR_MISALIGN_CSR_STORE_SPLIT_SUMMARY`
- `XS_SCALAR_MISALIGN_CSR_FORWARD_SUMMARY`
- `XS_SCALAR_MISALIGN_CSR_CROSS_SUMMARY`

每个 deterministic run snippet 在开始时清零自己的 summary CSR，在成功结束时写入：

- `((uint64_t) MAGIC << 32) | count`

其中：

- `load_split_templates` / `store_split_templates` 的 `count = 6`
- `store_forward_overlap` / `cross_page_faults` 的 `count = 2`

check 只读：

- 自己的 flags
- 自己的 summary CSR
- 自己已经独占的 value/cause CSR

不再依赖 `env->snippet_id` 作为 family combo 契约。

### 3.2 新增组合 Suites

第一波新增 3 个确定性 family-combo suites：

1. `scalar_misalign_templates_combo_poc`
   - run: `init_basic_env`, `load_split_templates`, `store_split_templates`
   - check: `check_load_split_templates`, `check_store_split_templates`, `finish_check`

2. `scalar_misalign_fault_forward_combo_poc`
   - run: `init_basic_env`, `store_forward_overlap`, `cross_page_faults`
   - check: `check_store_forward_overlap`, `check_cross_page_faults`, `finish_check`

3. `scalar_misalign_family_combo_poc`
   - run: `init_basic_env`, `load_split_templates`, `store_split_templates`, `store_forward_overlap`, `cross_page_faults`
   - check: `check_load_split_templates`, `check_store_split_templates`, `check_store_forward_overlap`, `check_cross_page_faults`, `finish_check`

所有新 suite 都使用 deferred-check schema：

```yaml
compose:
  mode: sequence
  run_snippets: ...
  check_snippets: ...
```

### 3.3 测试与验证

自动化覆盖分三层：

1. `tests/test_snippet_loading.py`
   - 新 suite 文件存在性
   - 新 suite deterministic plan

2. `tests/test_build_pipeline.py`
   - 新 suite 能 build 并生成正确 manifest/snippet 顺序

3. 真实 `emu`
   - 3 个新 suite 都单独运行
   - 验收标准统一为：
     - `status == "ran"`
     - `labels` 含 `good_trap`
     - `finish_code == 0`

## 4. 验收标准

- 现有 deterministic scalar-misalign suites 不退化
- `load_split` / `store_split` family checks 不再依赖 `env->snippet_id`
- 新增 3 个 family-combo suites
- 新增 3 个 family-combo suites 的 loading/build 测试
- 新增 3 个 family-combo suites 在真实 `emu` 上 `good_trap + finish_code=0`
- 最终回归桶保持全绿
