# Deferred Check Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add suite-level deferred check support so a suite can run multiple snippets first and then execute snippet `.check` callbacks in a separate final phase.

**Architecture:** Keep existing `compose.snippets` suites unchanged and add a second suite schema with `run_snippets` and `check_snippets`. Runtime gets two narrow helpers, `xsrt_run_snippet_no_check()` and `xsrt_run_snippet_check_only()`, while the emitter selects between legacy one-pass harness generation and the new two-phase harness. A dedicated integration suite proves that the same snippets can participate in both phases and only pass when checks are deferred.

**Tech Stack:** Python 3, `unittest`, C11 freestanding runtime, XiangShan `emu`, existing `snippetgen` YAML suite loader and harness emitter.

---

## File Map

- Modify: `generator/xsgen/model.py`
- Modify: `generator/xsgen/suite_loader.py`
- Modify: `generator/xsgen/emitter.py`
- Modify: `snippets/include/xs_snippet.h`
- Modify: `runtime/src/xsrt_snippet.c`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_runtime_surface.py`
- Modify: `tests/test_build_pipeline.py`
- Create: `snippets/deferred_check/deferred_mark_stage_a.c`
- Create: `snippets/deferred_check/deferred_mark_stage_b.c`
- Create: `snippets/manifests/deferred_mark_stage_a.yaml`
- Create: `snippets/manifests/deferred_mark_stage_b.yaml`
- Create: `suites/deferred_check_markers_poc.yaml`
- Create: `docs/2026-04-20-deferred-check-suite-run-notes.md`

## Scope Rules

- Do not change the semantics of existing `compose.snippets` suites.
- Do not add snippet-level `check_policy`.
- Do not delay `.fini`; `fini` remains attached to the run phase.
- The new schema must reject mixed use of `compose.snippets` with `compose.run_snippets` / `compose.check_snippets`.

### Task 1: Lock the New Suite Schema in Failing Tests

**Files:**
- Modify: `tests/test_snippet_loading.py`
- Modify: `generator/xsgen/model.py`
- Modify: `generator/xsgen/suite_loader.py`

- [ ] **Step 1: Add failing loader tests for the new schema**

```python
def test_suite_loader_accepts_deferred_check_schema(self) -> None:
    suite_loader = importlib.import_module("generator.xsgen.suite_loader")

    with tempfile.TemporaryDirectory() as tmpdir:
        suite_path = Path(tmpdir) / "deferred.yaml"
        suite_path.write_text(
            textwrap.dedent(
                """
                suite: deferred_suite
                target: xiangshan-verilator
                seed: 9
                compose:
                  mode: sequence
                  run_snippets:
                    - init_basic_env
                    - deferred_mark_stage_a
                    - deferred_mark_stage_b
                  check_snippets:
                    - deferred_mark_stage_a
                    - deferred_mark_stage_b
                    - finish_check
                """
            ).strip()
        )

        suite = suite_loader.load_suite(suite_path)

    self.assertEqual(("init_basic_env", "deferred_mark_stage_a", "deferred_mark_stage_b"), suite.run_snippet_ids)
    self.assertEqual(("deferred_mark_stage_a", "deferred_mark_stage_b", "finish_check"), suite.check_snippet_ids)
```

```python
def test_suite_loader_rejects_mixed_legacy_and_deferred_schema(self) -> None:
    suite_loader = importlib.import_module("generator.xsgen.suite_loader")

    with tempfile.TemporaryDirectory() as tmpdir:
        suite_path = Path(tmpdir) / "mixed.yaml"
        suite_path.write_text(
            textwrap.dedent(
                """
                suite: mixed_suite
                target: xiangshan-verilator
                seed: 9
                compose:
                  mode: sequence
                  snippets:
                    - init_basic_env
                  run_snippets:
                    - deferred_mark_stage_a
                  check_snippets:
                    - deferred_mark_stage_a
                """
            ).strip()
        )

        with self.assertRaisesRegex(ValueError, "cannot mix"):
            suite_loader.load_suite(suite_path)
```

```python
def test_build_compose_plan_preserves_deferred_phase_order(self) -> None:
    snippet_db = importlib.import_module("generator.xsgen.snippet_db")
    suite_loader = importlib.import_module("generator.xsgen.suite_loader")

    db = snippet_db.load_snippet_db(ROOT)
    suite = suite_loader.load_suite(ROOT / "suites/deferred_check_markers_poc.yaml")
    plan = suite_loader.build_compose_plan(suite, db)

    self.assertEqual(
        ("init_basic_env", "deferred_mark_stage_a", "deferred_mark_stage_b"),
        plan.run_snippet_ids,
    )
    self.assertEqual(
        ("deferred_mark_stage_a", "deferred_mark_stage_b", "finish_check"),
        plan.check_snippet_ids,
    )
```

- [ ] **Step 2: Extend the dataclasses in `generator/xsgen/model.py`**

```python
@dataclass(frozen=True)
class SuiteSpec:
    name: str
    target: str
    seed: int
    compose_mode: str
    snippet_ids: tuple[str, ...]
    run_snippet_ids: tuple[str, ...] | None = None
    check_snippet_ids: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ComposePlan:
    suite_name: str
    target: str
    seed: int
    snippet_ids: tuple[str, ...]
    snippets: tuple[SnippetSpec, ...]
    run_snippet_ids: tuple[str, ...] | None = None
    check_snippet_ids: tuple[str, ...] | None = None
```

- [ ] **Step 3: Update `suite_loader.py` to parse and validate both schemas**

```python
legacy_snippet_ids = compose.get("snippets")
run_snippet_ids = compose.get("run_snippets")
check_snippet_ids = compose.get("check_snippets")

legacy_present = legacy_snippet_ids is not None
deferred_present = run_snippet_ids is not None or check_snippet_ids is not None

if legacy_present and deferred_present:
    raise ValueError(f"{path} cannot mix compose.snippets with run_snippets/check_snippets")

if legacy_present:
    ...
    return SuiteSpec(
        ...,
        snippet_ids=tuple(legacy_snippet_ids),
    )

if not deferred_present:
    raise ValueError(f"{path} compose section requires snippets or run_snippets/check_snippets")

if not isinstance(run_snippet_ids, list) or not run_snippet_ids:
    raise ValueError(f"{path} field 'compose.run_snippets' must be a non-empty list")
if not isinstance(check_snippet_ids, list) or not check_snippet_ids:
    raise ValueError(f"{path} field 'compose.check_snippets' must be a non-empty list")
if not all(isinstance(item, str) and item for item in run_snippet_ids + check_snippet_ids):
    raise ValueError(f"{path} deferred compose contains an invalid snippet id")

all_ids = tuple(dict.fromkeys([*run_snippet_ids, *check_snippet_ids]))
return SuiteSpec(
    ...,
    snippet_ids=all_ids,
    run_snippet_ids=tuple(run_snippet_ids),
    check_snippet_ids=tuple(check_snippet_ids),
)
```

And in `build_compose_plan()`:

```python
return ComposePlan(
    suite_name=suite.name,
    target=suite.target,
    seed=suite.seed,
    snippet_ids=suite.snippet_ids,
    snippets=tuple(resolved_snippets),
    run_snippet_ids=suite.run_snippet_ids,
    check_snippet_ids=suite.check_snippet_ids,
)
```

- [ ] **Step 4: Run the loader tests and verify they fail before implementation**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_suite_loader_accepts_deferred_check_schema \
  tests.test_snippet_loading.SnippetLoadingTest.test_suite_loader_rejects_mixed_legacy_and_deferred_schema \
  tests.test_snippet_loading.SnippetLoadingTest.test_build_compose_plan_preserves_deferred_phase_order -v
```

Expected: FAIL because `SuiteSpec` and `ComposePlan` do not yet expose `run_snippet_ids` / `check_snippet_ids`, and the loader only understands `compose.snippets`.

- [ ] **Step 5: Run the loader tests again and verify they pass**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_suite_loader_accepts_deferred_check_schema \
  tests.test_snippet_loading.SnippetLoadingTest.test_suite_loader_rejects_mixed_legacy_and_deferred_schema \
  tests.test_snippet_loading.SnippetLoadingTest.test_build_compose_plan_preserves_deferred_phase_order -v
```

Expected: PASS.

- [ ] **Step 6: Commit the schema work**

```bash
git add generator/xsgen/model.py generator/xsgen/suite_loader.py tests/test_snippet_loading.py
git commit -m "feat: add deferred check suite schema"
```

### Task 2: Add Runtime Helpers for No-Check and Check-Only Execution

**Files:**
- Modify: `snippets/include/xs_snippet.h`
- Modify: `runtime/src/xsrt_snippet.c`
- Modify: `tests/test_runtime_surface.py`

- [ ] **Step 1: Add failing runtime-surface assertions**

```python
def test_runtime_headers_expose_deferred_check_helpers(self) -> None:
    snippet_h = (ROOT / "snippets/include/xs_snippet.h").read_text()

    self.assertIn("int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);", snippet_h)
    self.assertIn("int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);", snippet_h)
```

Add to the C smoke body:

```c
static int no_check_order[3];
static int no_check_count = 0;
static int check_only_count = 0;

static int no_check_init(xsrt_env_t *env) {
  no_check_order[no_check_count++] = 1;
  env->flags |= 0x10u;
  return 0;
}

static int no_check_run(xsrt_env_t *env) {
  no_check_order[no_check_count++] = 2;
  env->flags |= 0x20u;
  return 0;
}

static int no_check_check(xsrt_env_t *env) {
  (void) env;
  return 91;
}

static void no_check_fini(xsrt_env_t *env) {
  no_check_order[no_check_count++] = 3;
  env->flags |= 0x40u;
}

static int deferred_check(xsrt_env_t *env) {
  check_only_count += 1;
  return (env->flags & 0x70u) == 0x70u ? 0 : 92;
}
```

And in `main()`:

```c
const xsrt_snippet_desc_t deferred = {
  .id = "deferred",
  .init = no_check_init,
  .run = no_check_run,
  .check = no_check_check,
  .fini = no_check_fini,
};
const xsrt_snippet_desc_t deferred_check_desc = {
  .id = "deferred_check",
  .check = deferred_check,
};

if (xsrt_run_snippet_no_check(&env, &deferred) != 0) {
  return 31;
}
if (no_check_count != 3 || no_check_order[0] != 1 || no_check_order[1] != 2 || no_check_order[2] != 3) {
  return 32;
}
if (xsrt_run_snippet_check_only(&env, &deferred_check_desc) != 0) {
  return 33;
}
if (check_only_count != 1) {
  return 34;
}
```

- [ ] **Step 2: Add the new helper declarations to `xs_snippet.h`**

```c
int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
```

- [ ] **Step 3: Implement the helpers in `xsrt_snippet.c`**

```c
static int xsrt_run_snippet_parts(
    xsrt_env_t *env,
    const xsrt_snippet_desc_t *snippet,
    int run_init,
    int run_body,
    int run_check,
    int run_fini) {
  int rc;

  if (env == 0 || snippet == 0) {
    return -1;
  }

  if (run_init && snippet->init != 0) {
    rc = snippet->init(env);
    if (rc != 0) {
      if (run_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (run_body && snippet->run != 0) {
    rc = snippet->run(env);
    if (rc != 0) {
      if (run_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (run_check && snippet->check != 0) {
    rc = snippet->check(env);
    if (rc != 0) {
      if (run_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (run_fini && snippet->fini != 0) {
    snippet->fini(env);
  }

  return 0;
}

int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_parts(env, snippet, 1, 1, 1, 1);
}

int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_parts(env, snippet, 1, 1, 0, 1);
}

int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_parts(env, snippet, 0, 0, 1, 0);
}
```

- [ ] **Step 4: Run the runtime tests and verify they fail first**

Run:

```bash
python3 -m unittest \
  tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_headers_expose_minimal_api \
  tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_c_surfaces_cross_compile -v
```

Expected: FAIL until the new declarations and helper implementation exist.

- [ ] **Step 5: Run the runtime tests again and verify they pass**

Run:

```bash
python3 -m unittest \
  tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_headers_expose_minimal_api \
  tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_c_surfaces_cross_compile -v
```

Expected: PASS.

- [ ] **Step 6: Commit the runtime helper work**

```bash
git add snippets/include/xs_snippet.h runtime/src/xsrt_snippet.c tests/test_runtime_surface.py
git commit -m "feat: add deferred check runtime helpers"
```

### Task 3: Teach the Emitter to Generate Two-Phase Harnesses

**Files:**
- Modify: `generator/xsgen/emitter.py`
- Modify: `tests/test_build_pipeline.py`

- [ ] **Step 1: Add failing emitter tests for deferred-check suites**

```python
def test_emitter_generates_two_phase_harness_for_deferred_check_suite(self) -> None:
    emitter = importlib.import_module("generator.xsgen.emitter")
    snippet_db = importlib.import_module("generator.xsgen.snippet_db")
    suite_loader = importlib.import_module("generator.xsgen.suite_loader")
    toolchain = importlib.import_module("generator.xsgen.toolchain")

    suite = suite_loader.load_suite(ROOT / "suites/deferred_check_markers_poc.yaml")
    plan = suite_loader.build_compose_plan(suite, snippet_db.load_snippet_db(ROOT))
    artifact = toolchain.artifact_paths_for_suite(ROOT, suite.name)
    emitter.emit_harness(plan, artifact.generated_suite_path)
    harness = artifact.generated_suite_path.read_text()

    self.assertIn("xsrt_run_snippet_no_check(&env, &snippet_deferred_mark_stage_a);", harness)
    self.assertIn("xsrt_run_snippet_no_check(&env, &snippet_deferred_mark_stage_b);", harness)
    self.assertIn("xsrt_run_snippet_check_only(&env, &snippet_deferred_mark_stage_a);", harness)
    self.assertIn("xsrt_run_snippet_check_only(&env, &snippet_deferred_mark_stage_b);", harness)

    run_a = harness.index("xsrt_run_snippet_no_check(&env, &snippet_deferred_mark_stage_a);")
    run_b = harness.index("xsrt_run_snippet_no_check(&env, &snippet_deferred_mark_stage_b);")
    check_a = harness.index("xsrt_run_snippet_check_only(&env, &snippet_deferred_mark_stage_a);")
    check_b = harness.index("xsrt_run_snippet_check_only(&env, &snippet_deferred_mark_stage_b);")

    self.assertLess(run_a, run_b)
    self.assertLess(run_b, check_a)
    self.assertLess(check_a, check_b)
```

```python
def test_deferred_check_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_proc_check_suite_build(
        suite_path="suites/deferred_check_markers_poc.yaml",
        build_dir=self.deferred_check_markers_build_dir,
        suite_name="deferred_check_markers_poc",
        snippet_ids=[
            "init_basic_env",
            "deferred_mark_stage_a",
            "deferred_mark_stage_b",
            "finish_check",
        ],
    )
```

- [ ] **Step 2: Extend `setUp()` in `tests/test_build_pipeline.py`**

```python
self.deferred_check_markers_build_dir = ROOT / "build" / "deferred_check_markers_poc"
if self.deferred_check_markers_build_dir.exists():
    shutil.rmtree(self.deferred_check_markers_build_dir)
```

- [ ] **Step 3: Update `emit_harness()` to branch on phase-aware plans**

```python
if plan.run_snippet_ids is not None and plan.check_snippet_ids is not None:
    for snippet_id in plan.run_snippet_ids:
        symbol = descriptor_symbol(snippet_id)
        lines.extend(
            [
                f"  rc = xsrt_run_snippet_no_check(&env, &{symbol});",
                "  if (rc != 0) {",
                "    xsrt_finish_fail(&env, (unsigned long) rc);",
                "    return rc;",
                "  }",
                "",
            ]
        )
    for snippet_id in plan.check_snippet_ids:
        symbol = descriptor_symbol(snippet_id)
        lines.extend(
            [
                f"  rc = xsrt_run_snippet_check_only(&env, &{symbol});",
                "  if (rc != 0) {",
                "    xsrt_finish_fail(&env, (unsigned long) rc);",
                "    return rc;",
                "  }",
                "",
            ]
        )
else:
    for snippet_id in plan.snippet_ids:
        ...
```

- [ ] **Step 4: Run the emitter/build tests and watch them fail first**

Run:

```bash
python3 -m unittest \
  tests.test_build_pipeline.BuildPipelineTest.test_emitter_generates_two_phase_harness_for_deferred_check_suite \
  tests.test_build_pipeline.BuildPipelineTest.test_deferred_check_suite_build_generates_artifacts_and_manifest -v
```

Expected: FAIL until the emitter understands `run_snippet_ids` / `check_snippet_ids`.

- [ ] **Step 5: Run the emitter/build tests again and verify they pass**

Run:

```bash
python3 -m unittest \
  tests.test_build_pipeline.BuildPipelineTest.test_emitter_generates_two_phase_harness_for_deferred_check_suite \
  tests.test_build_pipeline.BuildPipelineTest.test_deferred_check_suite_build_generates_artifacts_and_manifest -v
```

Expected: PASS.

- [ ] **Step 6: Commit the emitter work**

```bash
git add generator/xsgen/emitter.py tests/test_build_pipeline.py
git commit -m "feat: emit two-phase harnesses for deferred checks"
```

### Task 4: Add an Integration Suite and Run It on XiangShan `emu`

**Files:**
- Create: `snippets/deferred_check/deferred_mark_stage_a.c`
- Create: `snippets/deferred_check/deferred_mark_stage_b.c`
- Create: `snippets/manifests/deferred_mark_stage_a.yaml`
- Create: `snippets/manifests/deferred_mark_stage_b.yaml`
- Create: `suites/deferred_check_markers_poc.yaml`
- Create: `docs/2026-04-20-deferred-check-suite-run-notes.md`
- Modify: `tests/test_snippet_loading.py`

- [ ] **Step 1: Add the new files to `tests/test_snippet_loading.py`**

```python
DEFERRED_CHECK_FILES = [
    "snippets/deferred_check/deferred_mark_stage_a.c",
    "snippets/deferred_check/deferred_mark_stage_b.c",
    "snippets/manifests/deferred_mark_stage_a.yaml",
    "snippets/manifests/deferred_mark_stage_b.yaml",
    "suites/deferred_check_markers_poc.yaml",
]


def test_deferred_check_files_exist(self) -> None:
    for relative_path in DEFERRED_CHECK_FILES:
        with self.subTest(path=relative_path):
            self.assertTrue((ROOT / relative_path).is_file())
```

- [ ] **Step 2: Create `deferred_mark_stage_a.c`**

```c
#include <stdint.h>

#include "xs_snippet.h"

enum {
  XS_DEFERRED_STAGE_A_RUN = 1u << 8,
  XS_DEFERRED_STAGE_A_FINI = 1u << 9,
  XS_DEFERRED_STAGE_B_RUN = 1u << 10,
  XS_DEFERRED_STAGE_B_FINI = 1u << 11,
};

static int deferred_mark_stage_a_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_DEFERRED_STAGE_A_RUN;
  env->snippet_id = 0xa1u;
  return 0;
}

static int deferred_mark_stage_a_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_A_RUN) == 0u) {
    return 501;
  }
  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_B_RUN) == 0u) {
    return 502;
  }
  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_B_FINI) == 0u) {
    return 503;
  }

  return 0;
}

static void deferred_mark_stage_a_fini(xsrt_env_t *env) {
  if (env == 0) {
    return;
  }

  env->flags |= (uint64_t) XS_DEFERRED_STAGE_A_FINI;
}

const xsrt_snippet_desc_t snippet_deferred_mark_stage_a = {
  .id = "deferred_mark_stage_a",
  .run = deferred_mark_stage_a_run,
  .check = deferred_mark_stage_a_check,
  .fini = deferred_mark_stage_a_fini,
};
```

- [ ] **Step 3: Create `deferred_mark_stage_b.c`**

```c
#include <stdint.h>

#include "xs_snippet.h"

enum {
  XS_DEFERRED_STAGE_A_RUN = 1u << 8,
  XS_DEFERRED_STAGE_A_FINI = 1u << 9,
  XS_DEFERRED_STAGE_B_RUN = 1u << 10,
  XS_DEFERRED_STAGE_B_FINI = 1u << 11,
};

static int deferred_mark_stage_b_run(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  env->flags |= (uint64_t) XS_DEFERRED_STAGE_B_RUN;
  env->snippet_id = 0xb2u;
  return 0;
}

static int deferred_mark_stage_b_check(xsrt_env_t *env) {
  if (env == 0) {
    return -1;
  }

  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_A_FINI) == 0u) {
    return 511;
  }
  if ((env->flags & (uint64_t) XS_DEFERRED_STAGE_B_RUN) == 0u) {
    return 512;
  }

  return 0;
}

static void deferred_mark_stage_b_fini(xsrt_env_t *env) {
  if (env == 0) {
    return;
  }

  env->flags |= (uint64_t) XS_DEFERRED_STAGE_B_FINI;
}

const xsrt_snippet_desc_t snippet_deferred_mark_stage_b = {
  .id = "deferred_mark_stage_b",
  .run = deferred_mark_stage_b_run,
  .check = deferred_mark_stage_b_check,
  .fini = deferred_mark_stage_b_fini,
};
```

- [ ] **Step 4: Create the manifests and suite**

```yaml
# snippets/manifests/deferred_mark_stage_a.yaml
id: deferred_mark_stage_a
kind: proc
lang: c
sources:
  - snippets/deferred_check/deferred_mark_stage_a.c
```

```yaml
# snippets/manifests/deferred_mark_stage_b.yaml
id: deferred_mark_stage_b
kind: proc
lang: c
sources:
  - snippets/deferred_check/deferred_mark_stage_b.c
```

```yaml
# suites/deferred_check_markers_poc.yaml
suite: deferred_check_markers_poc
target: xiangshan-verilator
seed: 8601
compose:
  mode: sequence
  run_snippets:
    - init_basic_env
    - deferred_mark_stage_a
    - deferred_mark_stage_b
  check_snippets:
    - deferred_mark_stage_a
    - deferred_mark_stage_b
    - finish_check
```

- [ ] **Step 5: Run the integration tests locally**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_deferred_check_files_exist \
  tests.test_build_pipeline.BuildPipelineTest.test_deferred_check_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_emitter_generates_two_phase_harness_for_deferred_check_suite \
  tests.test_runtime_surface.RuntimeSurfaceTest.test_runtime_c_surfaces_cross_compile -v
```

Expected: PASS.

- [ ] **Step 6: Run the new integration suite on real `emu`**

Run:

```bash
SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh \
python3 generator/cli.py run suites/deferred_check_markers_poc.yaml --seed 8601 --batch-id real_deferred_check_markers_8601
```

Expected:

```text
build/deferred_check_markers_poc/runs/real_deferred_check_markers_8601/batch_meta.json
```

And the batch entry must satisfy:

```text
status == "ran"
labels include "good_trap"
finish_code == 0
```

- [ ] **Step 7: Write the run notes**

```markdown
# Deferred Check Suite Run Notes

- `real_deferred_check_markers_8601`: `good_trap`, `finish_code=0`
- Evidence: `build/deferred_check_markers_poc/runs/real_deferred_check_markers_8601/batch_meta.json`
```

- [ ] **Step 8: Run the final focused regression bucket**

Run:

```bash
python3 -m unittest \
  tests.test_runtime_surface \
  tests.test_snippet_loading \
  tests.test_build_pipeline \
  tests.test_run_pipeline -v
```

Expected: PASS, except any unrelated pre-existing repo failures that also fail on `dev` before this feature.

- [ ] **Step 9: Commit the integration suite**

```bash
git add \
  snippets/deferred_check/deferred_mark_stage_a.c \
  snippets/deferred_check/deferred_mark_stage_b.c \
  snippets/manifests/deferred_mark_stage_a.yaml \
  snippets/manifests/deferred_mark_stage_b.yaml \
  suites/deferred_check_markers_poc.yaml \
  tests/test_snippet_loading.py \
  docs/2026-04-20-deferred-check-suite-run-notes.md
git commit -m "feat: add deferred check integration suite"
```

## Acceptance Criteria

- Existing `compose.snippets` suites remain untouched and continue to use `xsrt_run_snippet()`.
- New deferred suites can use `compose.run_snippets` and `compose.check_snippets`.
- Runtime exposes `xsrt_run_snippet_no_check()` and `xsrt_run_snippet_check_only()`.
- The emitter generates a two-phase harness for deferred suites.
- The same snippet can appear in both run and check phases.
- The integration suite `deferred_check_markers_poc` passes on real XiangShan `emu`.
