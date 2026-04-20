# Scalar Misalign Phase 1 Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run the Phase 1 scalar misalign smoke suites on XiangShan `emu`, covering same-16B and cross-16B scalar load/store semantics plus one minimal store-to-load overlap case.

**Architecture:** Phase 1 stays entirely on the existing `am_program` path so each case is a self-contained `main()` program with a direct pass/fail return code. The implementation adds five `snippets/programs/*_main.c` files, five manifests, five suites, and targeted repository tests that verify file existence, source shape, build output, and then real `emu` runs with stable batch IDs.

**Tech Stack:** C11 AM programs, `generator/cli.py`, XiangShan `emu`, Python `unittest`, existing `am_program` manifest/harness pipeline.

---

## File Map

- Create: `snippets/programs/scalar_misalign_load_in_16b_main.c`
- Create: `snippets/programs/scalar_misalign_load_cross_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_in_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_cross_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_load_overlap_main.c`
- Create: `snippets/manifests/scalar_misalign_load_in_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_load_cross_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_in_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_cross_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_load_overlap_main.yaml`
- Create: `suites/scalar_misalign_load_in_16b_poc.yaml`
- Create: `suites/scalar_misalign_load_cross_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_in_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_cross_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_load_overlap_poc.yaml`
- Create: `docs/2026-04-20-scalar-misalign-phase1-run-notes.md`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_am_program_snippet_build.py`

## Scope Rules

- Only Phase 1 is in scope for this plan.
- Do not add a shared `xs_scalar_misalign.h` header yet.
- Do not add `proc + check` snippets yet.
- Do not claim internal hardware facts such as “entered SMB/LMB” in test names or assertions. Phase 1 only checks software-visible outcomes.
- Every new suite must build through the existing `am_program` harness with `init_basic_env -> <program> -> finish_check`.

### Task 1: Lock the Phase 1 Repository Surface with Failing Tests

**Files:**
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_am_program_snippet_build.py`

- [ ] **Step 1: Add a new file list and existence test to `tests/test_snippet_loading.py`**

```python
SCALAR_MISALIGN_PHASE1_FILES = [
    "snippets/programs/scalar_misalign_load_in_16b_main.c",
    "snippets/programs/scalar_misalign_load_cross_16b_main.c",
    "snippets/programs/scalar_misalign_store_in_16b_main.c",
    "snippets/programs/scalar_misalign_store_cross_16b_main.c",
    "snippets/programs/scalar_misalign_store_load_overlap_main.c",
    "snippets/manifests/scalar_misalign_load_in_16b_main.yaml",
    "snippets/manifests/scalar_misalign_load_cross_16b_main.yaml",
    "snippets/manifests/scalar_misalign_store_in_16b_main.yaml",
    "snippets/manifests/scalar_misalign_store_cross_16b_main.yaml",
    "snippets/manifests/scalar_misalign_store_load_overlap_main.yaml",
    "suites/scalar_misalign_load_in_16b_poc.yaml",
    "suites/scalar_misalign_load_cross_16b_poc.yaml",
    "suites/scalar_misalign_store_in_16b_poc.yaml",
    "suites/scalar_misalign_store_cross_16b_poc.yaml",
    "suites/scalar_misalign_store_load_overlap_poc.yaml",
]


def test_scalar_misalign_phase1_files_exist(self) -> None:
    for relative_path in SCALAR_MISALIGN_PHASE1_FILES:
        with self.subTest(path=relative_path):
            self.assertTrue((ROOT / relative_path).is_file())
```

- [ ] **Step 2: Add a helper and five failing build tests to `tests/test_build_pipeline.py`**

```python
def assert_am_program_suite_build(
    self,
    *,
    suite_path: str,
    build_dir: Path,
    suite_name: str,
    snippet_id: str,
) -> None:
    result = subprocess.run(
        ["python3", "generator/cli.py", "build", suite_path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    self.assertEqual(0, result.returncode, msg=result.stderr)

    generated_suite = build_dir / "generated_suite.c"
    build_manifest = build_dir / "build_manifest.json"

    self.assertTrue(generated_suite.is_file())
    self.assertTrue(build_manifest.is_file())

    manifest = json.loads(build_manifest.read_text())
    self.assertEqual(suite_name, manifest["suite"])
    self.assertEqual(
        ["init_basic_env", snippet_id, "finish_check"],
        manifest["snippet_ids"],
    )
    self.assertIn(f"xsam_program_entry_{snippet_id}", generated_suite.read_text())


def test_scalar_misalign_load_in_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_am_program_suite_build(
        suite_path="suites/scalar_misalign_load_in_16b_poc.yaml",
        build_dir=self.scalar_misalign_load_in_16b_build_dir,
        suite_name="scalar_misalign_load_in_16b_poc",
        snippet_id="scalar_misalign_load_in_16b_main",
    )


def test_scalar_misalign_load_cross_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_am_program_suite_build(
        suite_path="suites/scalar_misalign_load_cross_16b_poc.yaml",
        build_dir=self.scalar_misalign_load_cross_16b_build_dir,
        suite_name="scalar_misalign_load_cross_16b_poc",
        snippet_id="scalar_misalign_load_cross_16b_main",
    )


def test_scalar_misalign_store_in_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_am_program_suite_build(
        suite_path="suites/scalar_misalign_store_in_16b_poc.yaml",
        build_dir=self.scalar_misalign_store_in_16b_build_dir,
        suite_name="scalar_misalign_store_in_16b_poc",
        snippet_id="scalar_misalign_store_in_16b_main",
    )


def test_scalar_misalign_store_cross_16b_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_am_program_suite_build(
        suite_path="suites/scalar_misalign_store_cross_16b_poc.yaml",
        build_dir=self.scalar_misalign_store_cross_16b_build_dir,
        suite_name="scalar_misalign_store_cross_16b_poc",
        snippet_id="scalar_misalign_store_cross_16b_main",
    )


def test_scalar_misalign_store_load_overlap_suite_build_generates_artifacts_and_manifest(self) -> None:
    self.assert_am_program_suite_build(
        suite_path="suites/scalar_misalign_store_load_overlap_poc.yaml",
        build_dir=self.scalar_misalign_store_load_overlap_build_dir,
        suite_name="scalar_misalign_store_load_overlap_poc",
        snippet_id="scalar_misalign_store_load_overlap_main",
    )
```

- [ ] **Step 3: Extend `setUp()` in `tests/test_build_pipeline.py` with the new build directories**

```python
self.scalar_misalign_load_in_16b_build_dir = ROOT / "build" / "scalar_misalign_load_in_16b_poc"
self.scalar_misalign_load_cross_16b_build_dir = ROOT / "build" / "scalar_misalign_load_cross_16b_poc"
self.scalar_misalign_store_in_16b_build_dir = ROOT / "build" / "scalar_misalign_store_in_16b_poc"
self.scalar_misalign_store_cross_16b_build_dir = ROOT / "build" / "scalar_misalign_store_cross_16b_poc"
self.scalar_misalign_store_load_overlap_build_dir = ROOT / "build" / "scalar_misalign_store_load_overlap_poc"

if self.scalar_misalign_load_in_16b_build_dir.exists():
    shutil.rmtree(self.scalar_misalign_load_in_16b_build_dir)
if self.scalar_misalign_load_cross_16b_build_dir.exists():
    shutil.rmtree(self.scalar_misalign_load_cross_16b_build_dir)
if self.scalar_misalign_store_in_16b_build_dir.exists():
    shutil.rmtree(self.scalar_misalign_store_in_16b_build_dir)
if self.scalar_misalign_store_cross_16b_build_dir.exists():
    shutil.rmtree(self.scalar_misalign_store_cross_16b_build_dir)
if self.scalar_misalign_store_load_overlap_build_dir.exists():
    shutil.rmtree(self.scalar_misalign_store_load_overlap_build_dir)
```

- [ ] **Step 4: Add source-shape expectations to `tests/test_am_program_snippet_build.py`**

```python
def assert_program_contains(self, relative_path: str, needles: tuple[str, ...]) -> None:
    sample = (ROOT / relative_path).read_text()
    for needle in needles:
        self.assertIn(needle, sample)


def test_scalar_misalign_load_in_16b_program_uses_unaligned_lw_and_ld_within_16b(self) -> None:
    self.assert_program_contains(
        "snippets/programs/scalar_misalign_load_in_16b_main.c",
        (
            "__attribute__((aligned(16)))",
            '"lw %0, 0(%1)"',
            '"ld %0, 0(%1)"',
            "const uint8_t *lw_ptr = base + 1u;",
            "const uint8_t *ld_ptr = base + 7u;",
        ),
    )


def test_scalar_misalign_load_cross_16b_program_uses_cross_boundary_ld(self) -> None:
    self.assert_program_contains(
        "snippets/programs/scalar_misalign_load_cross_16b_main.c",
        (
            "__attribute__((aligned(16)))",
            '"ld %0, 0(%1)"',
            "const uint8_t *ptr = base + 13u;",
            "return 11;",
        ),
    )


def test_scalar_misalign_store_in_16b_program_uses_unaligned_sw_and_sd_within_16b(self) -> None:
    self.assert_program_contains(
        "snippets/programs/scalar_misalign_store_in_16b_main.c",
        (
            '"sw %1, 0(%0)"',
            '"sd %1, 0(%0)"',
            "uint8_t *sw_ptr = base + 1u;",
            "uint8_t *sd_ptr = base + 7u;",
        ),
    )


def test_scalar_misalign_store_cross_16b_program_uses_cross_boundary_sw_and_sd(self) -> None:
    self.assert_program_contains(
        "snippets/programs/scalar_misalign_store_cross_16b_main.c",
        (
            "__attribute__((aligned(16)))",
            '"sw %1, 0(%0)"',
            '"sd %1, 0(%0)"',
            "uint8_t *sd_ptr = region_a + 15u;",
            "uint8_t *sw_ptr = region_b + 14u;",
        ),
    )


def test_scalar_misalign_store_load_overlap_program_reads_back_complete_value(self) -> None:
    self.assert_program_contains(
        "snippets/programs/scalar_misalign_store_load_overlap_main.c",
        (
            '"sd %1, 0(%0)"',
            '"ld %0, 0(%1)"',
            "uint8_t *store_ptr = base + 15u;",
            "const uint8_t *fragment_ptr = base + 16u;",
        ),
    )
```

- [ ] **Step 5: Run the new tests and verify they fail**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_scalar_misalign_phase1_files_exist \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_load_in_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_scalar_misalign_load_in_16b_program_uses_unaligned_lw_and_ld_within_16b -v
```

Expected: FAIL because the new files and suites do not exist yet.

- [ ] **Step 6: Commit the red tests**

```bash
git add tests/test_snippet_loading.py tests/test_build_pipeline.py tests/test_am_program_snippet_build.py
git commit -m "test: lock scalar misalign phase1 smoke surface"
```

### Task 2: Implement the Five Phase 1 AM Program Smoke Cases

**Files:**
- Create: `snippets/programs/scalar_misalign_load_in_16b_main.c`
- Create: `snippets/programs/scalar_misalign_load_cross_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_in_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_cross_16b_main.c`
- Create: `snippets/programs/scalar_misalign_store_load_overlap_main.c`
- Create: `snippets/manifests/scalar_misalign_load_in_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_load_cross_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_in_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_cross_16b_main.yaml`
- Create: `snippets/manifests/scalar_misalign_store_load_overlap_main.yaml`
- Create: `suites/scalar_misalign_load_in_16b_poc.yaml`
- Create: `suites/scalar_misalign_load_cross_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_in_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_cross_16b_poc.yaml`
- Create: `suites/scalar_misalign_store_load_overlap_poc.yaml`

- [ ] **Step 1: Create `scalar_misalign_load_in_16b_main.c`**

```c
#include <stdint.h>

static uint8_t scalar_misalign_load_in_16b_arena[32] __attribute__((aligned(16)));

static uint32_t scalar_misalign_load_lw(const void *ptr) {
  uint32_t value;

  __asm__ volatile(
      "lw %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

static uint64_t scalar_misalign_load_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

int main(void) {
  uint8_t *base = &scalar_misalign_load_in_16b_arena[0];
  const uint8_t *lw_ptr = base + 1u;
  const uint8_t *ld_ptr = base + 7u;
  uint32_t lw_value;
  uint64_t ld_value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_load_in_16b_arena); ++index) {
    scalar_misalign_load_in_16b_arena[index] = 0u;
  }

  lw_ptr[0] = 0x44u;
  lw_ptr[1] = 0x33u;
  lw_ptr[2] = 0x22u;
  lw_ptr[3] = 0x11u;
  lw_value = scalar_misalign_load_lw(lw_ptr);
  if (lw_value != 0x11223344u) {
    return 11;
  }

  ld_ptr[0] = 0x88u;
  ld_ptr[1] = 0x77u;
  ld_ptr[2] = 0x66u;
  ld_ptr[3] = 0x55u;
  ld_ptr[4] = 0x44u;
  ld_ptr[5] = 0x33u;
  ld_ptr[6] = 0x22u;
  ld_ptr[7] = 0x11u;
  ld_value = scalar_misalign_load_ld(ld_ptr);
  if (ld_value != 0x1122334455667788ull) {
    return 12;
  }

  return 0;
}
```

- [ ] **Step 2: Create `scalar_misalign_load_cross_16b_main.c`**

```c
#include <stdint.h>

static uint8_t scalar_misalign_load_cross_16b_arena[48] __attribute__((aligned(16)));

static uint64_t scalar_misalign_cross_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

int main(void) {
  uint8_t *base = &scalar_misalign_load_cross_16b_arena[0];
  const uint8_t *ptr = base + 13u;
  uint64_t value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_load_cross_16b_arena); ++index) {
    scalar_misalign_load_cross_16b_arena[index] = 0u;
  }

  ptr[0] = 0x88u;
  ptr[1] = 0x77u;
  ptr[2] = 0x66u;
  ptr[3] = 0x55u;
  ptr[4] = 0x44u;
  ptr[5] = 0x33u;
  ptr[6] = 0x22u;
  ptr[7] = 0x11u;

  value = scalar_misalign_cross_ld(ptr);
  if (value != 0x1122334455667788ull) {
    return 11;
  }

  return 0;
}
```

- [ ] **Step 3: Create `scalar_misalign_store_in_16b_main.c`**

```c
#include <stdint.h>

static uint8_t scalar_misalign_store_in_16b_arena[32] __attribute__((aligned(16)));

static void scalar_misalign_store_sw(void *ptr, uint32_t value) {
  __asm__ volatile(
      "sw %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static void scalar_misalign_store_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

int main(void) {
  uint8_t *base = &scalar_misalign_store_in_16b_arena[0];
  uint8_t *sw_ptr = base + 1u;
  uint8_t *sd_ptr = base + 7u;

  for (unsigned index = 0; index < sizeof(scalar_misalign_store_in_16b_arena); ++index) {
    scalar_misalign_store_in_16b_arena[index] = 0u;
  }

  scalar_misalign_store_sw(sw_ptr, 0x11223344u);
  if (sw_ptr[0] != 0x44u || sw_ptr[1] != 0x33u || sw_ptr[2] != 0x22u || sw_ptr[3] != 0x11u) {
    return 11;
  }

  scalar_misalign_store_sd(sd_ptr, 0x1122334455667788ull);
  if (sd_ptr[0] != 0x88u || sd_ptr[1] != 0x77u || sd_ptr[2] != 0x66u || sd_ptr[3] != 0x55u ||
      sd_ptr[4] != 0x44u || sd_ptr[5] != 0x33u || sd_ptr[6] != 0x22u || sd_ptr[7] != 0x11u) {
    return 12;
  }

  return 0;
}
```

- [ ] **Step 4: Create `scalar_misalign_store_cross_16b_main.c`**

```c
#include <stdint.h>

static uint8_t scalar_misalign_store_cross_16b_arena[64] __attribute__((aligned(16)));

static void scalar_misalign_store_sw(void *ptr, uint32_t value) {
  __asm__ volatile(
      "sw %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static void scalar_misalign_store_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

int main(void) {
  uint8_t *region_a = &scalar_misalign_store_cross_16b_arena[0];
  uint8_t *region_b = &scalar_misalign_store_cross_16b_arena[32];
  uint8_t *sd_ptr = region_a + 15u;
  uint8_t *sw_ptr = region_b + 14u;

  for (unsigned index = 0; index < sizeof(scalar_misalign_store_cross_16b_arena); ++index) {
    scalar_misalign_store_cross_16b_arena[index] = 0u;
  }

  scalar_misalign_store_sd(sd_ptr, 0x1122334455667788ull);
  if (sd_ptr[0] != 0x88u || sd_ptr[1] != 0x77u || sd_ptr[2] != 0x66u || sd_ptr[3] != 0x55u ||
      sd_ptr[4] != 0x44u || sd_ptr[5] != 0x33u || sd_ptr[6] != 0x22u || sd_ptr[7] != 0x11u) {
    return 11;
  }

  scalar_misalign_store_sw(sw_ptr, 0xaabbccddu);
  if (sw_ptr[0] != 0xddu || sw_ptr[1] != 0xccu || sw_ptr[2] != 0xbbu || sw_ptr[3] != 0xaau) {
    return 12;
  }

  return 0;
}
```

- [ ] **Step 5: Create `scalar_misalign_store_load_overlap_main.c`**

```c
#include <stdint.h>

static uint8_t scalar_misalign_store_load_overlap_arena[48] __attribute__((aligned(16)));

static void scalar_misalign_store_sd(void *ptr, uint64_t value) {
  __asm__ volatile(
      "sd %1, 0(%0)"
      :
      : "r"(ptr), "r"(value)
      : "memory");
}

static uint64_t scalar_misalign_load_ld(const void *ptr) {
  uint64_t value;

  __asm__ volatile(
      "ld %0, 0(%1)"
      : "=r"(value)
      : "r"(ptr)
      : "memory");
  return value;
}

int main(void) {
  uint8_t *base = &scalar_misalign_store_load_overlap_arena[0];
  uint8_t *store_ptr = base + 15u;
  const uint8_t *fragment_ptr = base + 16u;
  uint64_t value;

  for (unsigned index = 0; index < sizeof(scalar_misalign_store_load_overlap_arena); ++index) {
    scalar_misalign_store_load_overlap_arena[index] = 0u;
  }

  scalar_misalign_store_sd(store_ptr, 0x1122334455667788ull);
  value = scalar_misalign_load_ld(store_ptr);
  if (value != 0x1122334455667788ull) {
    return 11;
  }

  if (fragment_ptr[0] != 0x77u || fragment_ptr[1] != 0x66u || fragment_ptr[2] != 0x55u ||
      fragment_ptr[3] != 0x44u || fragment_ptr[4] != 0x33u || fragment_ptr[5] != 0x22u ||
      fragment_ptr[6] != 0x11u) {
    return 12;
  }

  return 0;
}
```

- [ ] **Step 6: Create the five manifests**

```yaml
# snippets/manifests/scalar_misalign_load_in_16b_main.yaml
id: scalar_misalign_load_in_16b_main
kind: am_program
lang: c
entry: main
sources:
  - snippets/programs/scalar_misalign_load_in_16b_main.c
```

```yaml
# snippets/manifests/scalar_misalign_load_cross_16b_main.yaml
id: scalar_misalign_load_cross_16b_main
kind: am_program
lang: c
entry: main
sources:
  - snippets/programs/scalar_misalign_load_cross_16b_main.c
```

```yaml
# snippets/manifests/scalar_misalign_store_in_16b_main.yaml
id: scalar_misalign_store_in_16b_main
kind: am_program
lang: c
entry: main
sources:
  - snippets/programs/scalar_misalign_store_in_16b_main.c
```

```yaml
# snippets/manifests/scalar_misalign_store_cross_16b_main.yaml
id: scalar_misalign_store_cross_16b_main
kind: am_program
lang: c
entry: main
sources:
  - snippets/programs/scalar_misalign_store_cross_16b_main.c
```

```yaml
# snippets/manifests/scalar_misalign_store_load_overlap_main.yaml
id: scalar_misalign_store_load_overlap_main
kind: am_program
lang: c
entry: main
sources:
  - snippets/programs/scalar_misalign_store_load_overlap_main.c
```

- [ ] **Step 7: Create the five suites**

```yaml
# suites/scalar_misalign_load_in_16b_poc.yaml
suite: scalar_misalign_load_in_16b_poc
target: xiangshan-verilator
seed: 8301
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - scalar_misalign_load_in_16b_main
    - finish_check
```

```yaml
# suites/scalar_misalign_load_cross_16b_poc.yaml
suite: scalar_misalign_load_cross_16b_poc
target: xiangshan-verilator
seed: 8302
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - scalar_misalign_load_cross_16b_main
    - finish_check
```

```yaml
# suites/scalar_misalign_store_in_16b_poc.yaml
suite: scalar_misalign_store_in_16b_poc
target: xiangshan-verilator
seed: 8303
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - scalar_misalign_store_in_16b_main
    - finish_check
```

```yaml
# suites/scalar_misalign_store_cross_16b_poc.yaml
suite: scalar_misalign_store_cross_16b_poc
target: xiangshan-verilator
seed: 8304
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - scalar_misalign_store_cross_16b_main
    - finish_check
```

```yaml
# suites/scalar_misalign_store_load_overlap_poc.yaml
suite: scalar_misalign_store_load_overlap_poc
target: xiangshan-verilator
seed: 8305
compose:
  mode: sequence
  snippets:
    - init_basic_env
    - scalar_misalign_store_load_overlap_main
    - finish_check
```

- [ ] **Step 8: Run the targeted test subset and make it pass**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_scalar_misalign_phase1_files_exist \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_load_in_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_load_cross_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_in_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_cross_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_load_overlap_suite_build_generates_artifacts_and_manifest \
  tests.test_am_program_snippet_build -v
```

Expected: PASS.

- [ ] **Step 9: Commit the Phase 1 implementation**

```bash
git add \
  snippets/programs/scalar_misalign_load_in_16b_main.c \
  snippets/programs/scalar_misalign_load_cross_16b_main.c \
  snippets/programs/scalar_misalign_store_in_16b_main.c \
  snippets/programs/scalar_misalign_store_cross_16b_main.c \
  snippets/programs/scalar_misalign_store_load_overlap_main.c \
  snippets/manifests/scalar_misalign_load_in_16b_main.yaml \
  snippets/manifests/scalar_misalign_load_cross_16b_main.yaml \
  snippets/manifests/scalar_misalign_store_in_16b_main.yaml \
  snippets/manifests/scalar_misalign_store_cross_16b_main.yaml \
  snippets/manifests/scalar_misalign_store_load_overlap_main.yaml \
  suites/scalar_misalign_load_in_16b_poc.yaml \
  suites/scalar_misalign_load_cross_16b_poc.yaml \
  suites/scalar_misalign_store_in_16b_poc.yaml \
  suites/scalar_misalign_store_cross_16b_poc.yaml \
  suites/scalar_misalign_store_load_overlap_poc.yaml \
  tests/test_snippet_loading.py \
  tests/test_build_pipeline.py \
  tests/test_am_program_snippet_build.py
git commit -m "feat: add scalar misalign phase1 smoke suites"
```

### Task 3: Run the Five Smoke Suites on XiangShan `emu` and Record Evidence

**Files:**
- Create: `docs/2026-04-20-scalar-misalign-phase1-run-notes.md`

- [ ] **Step 1: Run the five smoke suites on real `emu`**

Run:

```bash
python3 generator/cli.py run suites/scalar_misalign_load_in_16b_poc.yaml --seed 8301 --batch-id real_scalar_misalign_load_in_16b_8301
python3 generator/cli.py run suites/scalar_misalign_load_cross_16b_poc.yaml --seed 8302 --batch-id real_scalar_misalign_load_cross_16b_8302
python3 generator/cli.py run suites/scalar_misalign_store_in_16b_poc.yaml --seed 8303 --batch-id real_scalar_misalign_store_in_16b_8303
python3 generator/cli.py run suites/scalar_misalign_store_cross_16b_poc.yaml --seed 8304 --batch-id real_scalar_misalign_store_cross_16b_8304
python3 generator/cli.py run suites/scalar_misalign_store_load_overlap_poc.yaml --seed 8305 --batch-id real_scalar_misalign_store_load_overlap_8305
```

Expected:

```text
<batch_meta.json path>
```

And each run must satisfy:

```text
status == "ran"
labels include "good_trap"
finish_code == 0
```

- [ ] **Step 2: Write the run notes file**

```markdown
# Scalar Misalign Phase 1 Run Notes

## Suites

- `scalar_misalign_load_in_16b_poc`
- `scalar_misalign_load_cross_16b_poc`
- `scalar_misalign_store_in_16b_poc`
- `scalar_misalign_store_cross_16b_poc`
- `scalar_misalign_store_load_overlap_poc`

## Real Run Results

- `real_scalar_misalign_load_in_16b_8301`: `good_trap`
- `real_scalar_misalign_load_cross_16b_8302`: `good_trap`
- `real_scalar_misalign_store_in_16b_8303`: `good_trap`
- `real_scalar_misalign_store_cross_16b_8304`: `good_trap`
- `real_scalar_misalign_store_load_overlap_8305`: `good_trap`

## Evidence Paths

- `build/scalar_misalign_load_in_16b_poc/runs/real_scalar_misalign_load_in_16b_8301/batch_meta.json`
- `build/scalar_misalign_load_cross_16b_poc/runs/real_scalar_misalign_load_cross_16b_8302/batch_meta.json`
- `build/scalar_misalign_store_in_16b_poc/runs/real_scalar_misalign_store_in_16b_8303/batch_meta.json`
- `build/scalar_misalign_store_cross_16b_poc/runs/real_scalar_misalign_store_cross_16b_8304/batch_meta.json`
- `build/scalar_misalign_store_load_overlap_poc/runs/real_scalar_misalign_store_load_overlap_8305/batch_meta.json`
```

- [ ] **Step 3: Run the final local verification bucket**

Run:

```bash
python3 -m unittest \
  tests.test_snippet_loading.SnippetLoadingTest.test_scalar_misalign_phase1_files_exist \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_load_in_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_load_cross_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_in_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_cross_16b_suite_build_generates_artifacts_and_manifest \
  tests.test_build_pipeline.BuildPipelineTest.test_scalar_misalign_store_load_overlap_suite_build_generates_artifacts_and_manifest \
  tests.test_am_program_snippet_build \
  tests.test_run_pipeline -v
```

Expected: PASS.

- [ ] **Step 4: Commit the run notes**

```bash
git add docs/2026-04-20-scalar-misalign-phase1-run-notes.md
git commit -m "docs: record scalar misalign phase1 emu runs"
```

## Acceptance Criteria

- Five new Phase 1 scalar misalign AM-program snippets exist with manifests and suites.
- `tests/test_snippet_loading.py` tracks the new files.
- `tests/test_build_pipeline.py` can build all five suites and confirms harness order via `build_manifest.json`.
- `tests/test_am_program_snippet_build.py` asserts the intended load/store instruction shapes.
- All five suites complete one real XiangShan `emu` run with `good_trap` and `finish_code == 0`.
- Run evidence is recorded in `docs/2026-04-20-scalar-misalign-phase1-run-notes.md`.
