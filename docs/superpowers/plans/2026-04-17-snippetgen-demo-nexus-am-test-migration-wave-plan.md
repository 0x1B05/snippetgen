# SnippetGen Demo Nexus-AM Test Migration Wave Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate a staged set of existing `nexus-am` tests into `snippetgen-demo` as `main()`-style AM program snippets and verify they build and run on XiangShan/NEMU through the repository workflow.

**Architecture:** Migrate tests in ascending risk order. Start with self-contained `cputest` cases, then move to fault-side `memscantest` subcases that require local trap/PMP/MPRV setup, and only then grow toward fetch-fault/page-fault/VME-oriented variants. Keep each migrated case as one standalone `am_program` snippet wrapped by the existing generator/runtime shell.

**Tech Stack:** C baremetal AM programs, YAML manifests/suites, Python generator/CLI, XiangShan `emu`, NEMU diff, `unittest`.

---

## File Structure

- Existing reusable runtime/generator base:
  - `runtime/include/xsam/*`
  - `runtime/src/xsam_*`
  - `runtime/src/xsrt_*`
  - `generator/xsgen/*`
- Migrated test programs:
  - `snippets/programs/nexus_cputest_unalign_main.c`
  - `snippets/programs/nexus_cputest_load_store_main.c`
  - `snippets/programs/nexus_memscan_access_fault_main.c`
- Manifests:
  - `snippets/manifests/nexus_cputest_unalign_main.yaml`
  - `snippets/manifests/nexus_cputest_load_store_main.yaml`
  - `snippets/manifests/nexus_memscan_access_fault_main.yaml`
- Suites:
  - `suites/nexus_cputest_unalign_poc.yaml`
  - `suites/nexus_cputest_load_store_poc.yaml`
  - `suites/nexus_memscan_access_fault_poc.yaml`
- Regression coverage:
  - `tests/test_snippet_loading.py`
  - `tests/test_build_pipeline.py`
  - `tests/test_am_program_snippet_build.py`

## Migration Order

### Task 1: Migrate low-risk `cputest` AM programs

**Files:**
- Create: `snippets/programs/nexus_cputest_unalign_main.c`
- Create: `snippets/programs/nexus_cputest_load_store_main.c`
- Create: `snippets/manifests/nexus_cputest_unalign_main.yaml`
- Create: `snippets/manifests/nexus_cputest_load_store_main.yaml`
- Create: `suites/nexus_cputest_unalign_poc.yaml`
- Create: `suites/nexus_cputest_load_store_poc.yaml`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`

- [x] Write failing file/build tests for the two migrated `cputest` cases.
- [x] Add the two AM program sources and their manifests/suites.
- [x] Verify build with:
  - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist`
  - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest`
  - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest`
- [x] Verify real runs with:
  - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_cputest_unalign_poc.yaml --seed 8193 --batch-id real_nexus_cputest_unalign_8193 --timeout-sec 180`
  - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_cputest_load_store_poc.yaml --seed 8194 --batch-id real_nexus_cputest_load_store_8194 --timeout-sec 180`

### Task 2: Migrate first `memscantest` fault subcase

**Files:**
- Create: `snippets/programs/nexus_memscan_access_fault_main.c`
- Create: `snippets/manifests/nexus_memscan_access_fault_main.yaml`
- Create: `suites/nexus_memscan_access_fault_poc.yaml`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_am_program_snippet_build.py`

- [x] Write failing file/build tests for the `memscantest`-derived access-fault case.
- [x] Add a minimal AM program that:
  - installs a trap handler
  - configures a PMP deny window matching `nexus-am` expectations
  - probes the deny window under `MPRV + MPP=S`
  - validates both load-access-fault and store-access-fault
- [x] Verify build with:
  - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
  - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest`
  - `python3 -m unittest tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_nexus_memscan_program_uses_pmp_and_mprv_for_fault_probe`
- [x] Verify real run with:
  - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_memscan_access_fault_poc.yaml --seed 8195 --batch-id real_nexus_memscan_access_fault_8195_fix3 --timeout-sec 180`

### Task 3: Grow fault-side coverage toward fetch/page-fault/VME

**Files:**
- Create: `snippets/programs/nexus_memscan_fetch_fault_main.c`
- Create: `snippets/programs/nexus_memscan_page_fault_main.c`
- Create: `snippets/manifests/nexus_memscan_fetch_fault_main.yaml`
- Create: `snippets/manifests/nexus_memscan_page_fault_main.yaml`
- Create: `suites/nexus_memscan_fetch_fault_poc.yaml`
- Create: `suites/nexus_memscan_page_fault_poc.yaml`
- Modify: `runtime/src/xsam_vme.c`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_am_program_snippet_build.py`

- [x] Write failing tests for fetch-fault migration first.
- [x] Port one `memscantest` execute-fault subcase, keeping trap accounting explicit.
- [x] Run local build/unit regressions.
- [x] Run one real XiangShan/NEMU execution and classify the result.
- [x] Only after fetch-fault is stable, start a first page-fault/VME-oriented migrated case.
  - Added `snippets/programs/nexus_memscan_page_fault_main.c` plus manifest/suite.
  - The migrated Sv39 page-fault slice now installs a permissive S-mode PMP window before `MPRV + MPP=S` probes, so translated accesses hit page-table permissions instead of default S-mode PMP denial.
  - Verified with:
    - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `python3 -m unittest tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_nexus_memscan_page_fault_program_uses_sv39_satp_and_mprv_probes`
    - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest`
    - `python3 -m unittest tests.test_runtime_surface tests.test_xsam_cte_behavior tests.test_platform_driver_layer tests.test_xsam_vme_behavior tests.test_am_program_snippet_runtime tests.test_am_program_snippet_build tests.test_am_program_snippet_run tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_am_timer_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest tests.test_snippet_loading.SnippetLoadingTest.test_am_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_am_timer_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
  - Verified real run with:
    - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_memscan_page_fault_poc.yaml --seed 8197 --batch-id real_nexus_memscan_page_fault_8197_fix1 --timeout-sec 180`

### Task 4: Port a first Sv39 hugepage-oriented migrated case

**Files:**
- Create: `snippets/programs/nexus_memscan_hugepage_main.c`
- Create: `snippets/manifests/nexus_memscan_hugepage_main.yaml`
- Create: `suites/nexus_memscan_hugepage_poc.yaml`
- Modify: `tests/test_build_pipeline.py`
- Modify: `tests/test_snippet_loading.py`
- Modify: `tests/test_am_program_snippet_build.py`

- [x] Write failing file/build/source-shape tests for a minimal hugepage case.
- [x] Port the smallest `sv39_hp_atom_test` slice that proves one 2 MiB hugepage mapping works and one hugepage permission fault is delivered.
- [x] Reuse the page-fault PMP allow-all setup so MPRV+S accesses reach DRAM-backed hugepages.
- [x] Run local build/unit regressions.
- [x] Run one real XiangShan/NEMU execution and classify the result.
  - Added `snippets/programs/nexus_memscan_hugepage_main.c` plus manifest/suite.
  - The migrated hugepage slice covers:
    - RW 2 MiB hugepage write/read success
    - 4 KiB normal alias readback from the same backing physical region
    - RO hugepage store page fault delivery
  - Verified with:
    - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `python3 -m unittest tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_nexus_memscan_hugepage_program_uses_level1_leaf_mapping`
    - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest`
    - `python3 -m unittest tests.test_runtime_surface tests.test_xsam_cte_behavior tests.test_platform_driver_layer tests.test_xsam_vme_behavior tests.test_am_program_snippet_runtime tests.test_am_program_snippet_build tests.test_am_program_snippet_run tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_am_timer_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest tests.test_snippet_loading.SnippetLoadingTest.test_am_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_am_timer_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
  - Verified real run with:
    - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_memscan_hugepage_poc.yaml --seed 8198 --batch-id real_nexus_memscan_hugepage_8198_fix1 --timeout-sec 180`

## Current Acceptance State

- [x] Existing `nexus-am` tests migrated and real-run verified:
  - `cputest/unalign`
  - `cputest/load-store`
  - `memscantest` minimal load/store access-fault slice
  - `memscantest` execute-fault slice
  - `memscantest` first Sv39 page-fault slice
  - `memscantest` first Sv39 hugepage slice
- [x] Repository regression command currently passing:
  - `python3 -m unittest tests.test_runtime_surface tests.test_xsam_cte_behavior tests.test_platform_driver_layer tests.test_xsam_vme_behavior tests.test_am_program_snippet_runtime tests.test_am_program_snippet_build tests.test_am_program_snippet_run tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_am_timer_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest tests.test_snippet_loading.SnippetLoadingTest.test_am_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_am_timer_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
- [x] Follow-on hugepage access-fault slice migrated and real-run verified:
  - `snippets/programs/nexus_memscan_hugepage_access_fault_main.c`
  - `snippets/manifests/nexus_memscan_hugepage_access_fault_main.yaml`
  - `suites/nexus_memscan_hugepage_access_fault_poc.yaml`
  - Verified with:
    - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `python3 -m unittest tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_nexus_memscan_hugepage_access_fault_program_uses_huge_leaf_and_pmp_deny_window`
    - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_access_fault_suite_build_generates_artifacts_and_manifest`
    - `python3 -m unittest tests.test_runtime_surface tests.test_xsam_cte_behavior tests.test_platform_driver_layer tests.test_xsam_vme_behavior tests.test_am_program_snippet_runtime tests.test_am_program_snippet_build tests.test_am_program_snippet_run tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_am_timer_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_access_fault_suite_build_generates_artifacts_and_manifest tests.test_snippet_loading.SnippetLoadingTest.test_am_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_am_timer_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_memscan_hugepage_access_fault_poc.yaml --seed 8199 --batch-id real_nexus_memscan_hugepage_access_fault_8199_fix1 --timeout-sec 180`
- [x] Follow-on hugepage atom-fault slice migrated and real-run verified:
  - `snippets/programs/nexus_memscan_hugepage_atom_fault_main.c`
  - `snippets/manifests/nexus_memscan_hugepage_atom_fault_main.yaml`
  - `suites/nexus_memscan_hugepage_atom_fault_poc.yaml`
  - The migrated atom slice covers:
    - one working RW hugepage AMO/LR path
    - `amoadd.d` on an R-only hugepage triggering store page fault
    - `lr.d` on a W-only hugepage triggering load page fault
  - Verified with:
    - `python3 -m unittest tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `python3 -m unittest tests.test_am_program_snippet_build.AMProgramSnippetBuildTest.test_nexus_memscan_hugepage_atom_fault_program_uses_amo_lr_and_huge_leafs`
    - `python3 -m unittest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_atom_fault_suite_build_generates_artifacts_and_manifest`
    - `python3 -m unittest tests.test_runtime_surface tests.test_xsam_cte_behavior tests.test_platform_driver_layer tests.test_xsam_vme_behavior tests.test_am_program_snippet_runtime tests.test_am_program_snippet_build tests.test_am_program_snippet_run tests.test_build_pipeline.BuildPipelineTest.test_am_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_am_timer_program_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_unalign_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_cputest_load_store_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_fetch_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_page_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_access_fault_suite_build_generates_artifacts_and_manifest tests.test_build_pipeline.BuildPipelineTest.test_nexus_memscan_hugepage_atom_fault_suite_build_generates_artifacts_and_manifest tests.test_snippet_loading.SnippetLoadingTest.test_am_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_am_timer_program_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_cputest_port_files_exist tests.test_snippet_loading.SnippetLoadingTest.test_nexus_memscan_port_files_exist`
    - `SNIPPETGEN_XS_ENV_SH=/home/dfpmts/XS/xs-env/env.sh SNIPPETGEN_RUN_MAX_CYCLES=200000 SNIPPETGEN_RUN_MAX_INSTR=200000 python3 generator/cli.py run suites/nexus_memscan_hugepage_atom_fault_poc.yaml --seed 8200 --batch-id real_nexus_memscan_hugepage_atom_fault_8200_fix1 --timeout-sec 180`
- [ ] Next target not yet migrated:
  - remaining `sv39_test` / `sv39_hp_atom_test` edge cases outside the minimal baseline set
