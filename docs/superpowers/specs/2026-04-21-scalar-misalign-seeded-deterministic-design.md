# Scalar Misalign Seeded Deterministic Design

**Date:** 2026-04-21

**Goal**

为 `scalar_misalign` 家族中的 deterministic snippets 增加基于 `seed` 的参数扰动，
在保持严格 `pass/fail` 语义不变的前提下，提高每个 suite 的覆盖强度。

**Scope**

- 只改 deterministic snippets：
  - `load_split_templates`
  - `store_split_templates`
  - `store_forward_overlap`
  - `cross_page_faults`
- 不改 `search/probe` snippets
- 不新增新的 suite schema

## Design

### 1. 总原则

- `seed` 只改变参数，不改变语义集合
- 每个 `seed` 仍然必须 `good_trap + finish_code=0`
- `check` 仍然是严格断言，不退化为 probe

### 2. 具体扰动

#### `load_split_templates`

- `seed` 控制：
  - case 轮转顺序
  - arena bank 选择
  - 重复轮次
- 运行结果通过 summary CSR 编码：
  - `magic`
  - `rounds`
  - `rotation`
  - `bank_seed`
  - `total_cases`

#### `store_split_templates`

- `seed` 控制：
  - case 轮转顺序
  - arena bank 选择
  - 重复轮次
- summary CSR 编码与 `load_split_templates` 对称

#### `store_forward_overlap`

- `seed` 控制：
  - slot pair 选择
  - pre-skid 次数
  - between-skid 次数
  - 重复轮次
  - target/blocker value 扰动
- check 重新根据 `seed` 计算最后一轮期望值和 summary

#### `cross_page_faults`

- `seed` 控制：
  - 重复轮次
  - load/store offset 选择
  - fault 前窗口字节填充
- 为避免 `limit_exceeded`，只填 fault 边界附近的小窗口，不再整页填充

### 3. 验证策略

- 本地回归：
  - source-contract tests
  - loading/build bucket
  - full `runtime + loading + build + run` bucket
- 真实 `emu`：
  - 4 个 standalone deterministic suites
  - 3 个 family combo suites
- 证据：
  - `docs/evidence/scalar-misalign-seeded-deterministic/*.json`

## Acceptance

- 4 个 deterministic snippets 现在显式使用 `env->seed`
- 现有 deterministic suites 继续 build/run 正常
- 相关 family combo suites 在非默认 seed 下继续 `good_trap`
- `python3 -m unittest tests.test_runtime_surface tests.test_snippet_loading tests.test_build_pipeline tests.test_run_pipeline -v` 全绿
