# Random Suite Generation Design

**Date:** 2026-04-21

**Goal**

为 `snippetgen-demo` 增加一个可以随机生成 deferred-check suite YAML 的功能。
第一版只支持内置 pool，并先落地 `scalar_misalign_full`。

## Scope

- 新增 CLI：
  - `list-suite-pools`
  - `generate-suites`
- 支持内置 pool：`scalar_misalign_full`
- 一次生成 `N` 个 deferred-check suites
- 自动注入：
  - `init_basic_env`
  - `finish_check`
- 生成结果需要可直接被 `build` / `run`

## Non-Goal

- 第一版不支持任意用户自定义 pool
- 第一版不做“生成后自动批跑”
- 第一版不做权重规则引擎

## Design

### 1. Pool

`scalar_misalign_full`:

- run pool:
  - `load_split_templates`
  - `store_split_templates`
  - `store_forward_overlap`
  - `cross_page_faults`
- check map:
  - `load_split_templates -> check_load_split_templates`
  - `store_split_templates -> check_store_split_templates`
  - `store_forward_overlap -> check_store_forward_overlap`
  - `cross_page_faults -> check_cross_page_faults`

### 2. CLI

`list-suite-pools`

- prints all built-in pool names

`generate-suites`

- `--pool`
- `--count`
- `--run-count`
- `--seed`
- `--output-dir`
- `--prefix`

### 3. Output

生成器输出：

- `N` 个 YAML suite
- 一个 batch JSON，记录：
  - generator seed
  - selected pool
  - suite count
  - run count
  - each suite path
  - each suite runtime seed
  - chosen run/check snippets

### 4. Deferred-check shape

每个生成 suite 统一是：

```yaml
compose:
  mode: sequence
  run_snippets:
    - init_basic_env
    - ...
  check_snippets:
    - ...
    - finish_check
```

### 5. Acceptance

- CLI can list pools
- CLI can generate `N` deferred-check suites
- Generated suites round-trip through suite loader
- Generated suites can build
- A generated batch for `scalar_misalign_full` can be run on real `emu`
