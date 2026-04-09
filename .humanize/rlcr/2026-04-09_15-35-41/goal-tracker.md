# Goal Tracker

<!--
This file tracks the ultimate goal, acceptance criteria, and plan evolution.
It prevents goal drift by maintaining a persistent anchor across all rounds.

RULES:
- IMMUTABLE SECTION: Do not modify after initialization
- MUTABLE SECTION: Update each round, but document all changes
- Every task must be in one of: Active, Completed, or Deferred
- Deferred items require explicit justification
-->

## IMMUTABLE SECTION
<!-- Do not modify after initialization -->

### Ultimate Goal

实现一个最小可执行 PoC，证明 `SnippetGen` 的基础生成链路成立：能够读取 `suite.yaml` 和 `snippet manifests`，定位 snippet 源文件，自动生成 harness，并用 RISC-V 交叉工具链稳定产出 `ELF` 与 `bin` 文件。

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->

- AC-1: 给定合法的 suite 和 snippet manifests，工具能稳定解析出确定性的 `sequence` 执行计划；若引用不存在的 snippet、缺少必要字段或使用未实现的组合模式，必须在 planning/loading 阶段明确失败。
- AC-2: 生成器必须根据 suite 自动发射 `build/<suite>/generated_suite.c`，并把 runtime 与所有被引用 snippet 接到同一个编译目标；禁止用固定手写 main 伪装自动生成。
- AC-3: 最小 runtime C API 与 `xsrt_snippet_desc_t` ABI 足以支撑第一阶段的少量 `proc snippet` 编译；不允许依赖未冻结的高级 API 或隐式寄存器协商。
- AC-4: 默认构建路径必须稳定地产出 `build/<suite>/test.elf`、`build/<suite>/test.bin` 和 `build/<suite>/build_manifest.json`；链接或 `objcopy` 失败时不得把任务视为成功。

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 5 (Updated: Round 2)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initialized tracker from `detail-plan.md` and normalized the ACs into four independent checks | Preserve the original scope while making future round reviews easier | No scope change; AC-1 to AC-4 remain intact |
| 0 | Narrowed the active implementation focus to `task1` after RLCR bootstrap completed in the same round | The loop remained on Round 0, so the round needed one concrete mainline coding objective | No scope change; only execution focus moved to the first planned task |
| 1 | Re-anchored to the Codex review result and set Round 1 mainline work to the runtime baseline plus snippet ABI | The first review verified `task1` and identified AC-2 and AC-3 as the next missing mainline work | No scope change; execution focus moved from scaffolding to the minimal runtime interface |
| 1 | Codex verified `task2` and `task3`, but rejected treating `task4` through `task12` as queued follow-up work | The original plan's lower bound still requires snippets, manifests, suite loading, harness generation, and stable `ELF/bin` artifacts before the first-stage PoC is complete | No scope change; the next round must resume the end-to-end chain for AC-1, AC-2, and AC-4 |
| 2 | Re-anchored Round 2 to the snippet/manifests plus loading-layer milestone (`task4` through `task7`) | The latest review identified AC-1 and the remaining AC-3 work as the next concrete prerequisite for emitter and toolchain work | No scope change; execution focus moves from runtime baseline to plan inputs and deterministic loading |
| 2 | Fixed the misleading `make build` no-op by routing `build` through `generator/cli.py`, which now fails explicitly until the emitter and toolchain land | The prior review flagged the silent green build target as blocking future AC-4 verification | No scope change; the fix only removes a false-positive path and keeps later build work honest |

#### Active Tasks
<!-- Mainline tasks only: each task must directly advance the current round objective and carry routing metadata -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| task8: Implement `emitter.py` to generate `build/<suite>/generated_suite.c` from the ordered snippet list | AC-2 | pending | coding | claude | Depends on task6 and task7 |
| task9: Implement `toolchain.py` to compile runtime/snippet/harness sources, link `test.elf`, and export `test.bin` | AC-4 | pending | coding | claude | Depends on task2, task4, and task8 |
| task10: Create `scalar_load_legality_poc.yaml` and verify the build path generates `test.elf`, `test.bin`, and `build_manifest.json` | AC-1, AC-4 | pending | coding | claude | First end-to-end proof point |
| task11: Add unit tests for manifest loading, suite loading, and harness emission failure modes | AC-1, AC-2 | pending | coding | claude | Lock down deterministic behavior |
| task12: Review produced artifacts and prune any accidental future-only dependencies | AC-3, AC-4 | pending | analyze | codex | Run only after artifacts exist |

### Blocking Side Issues
<!-- Only issues that directly block current mainline progress belong here -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| None | - | - | - |

### Queued Side Issues
<!-- Non-blocking issues stay queued and must NOT replace the round objective -->
| Issue | Discovered Round | Why Not Blocking | Revisit Trigger |
|-------|-----------------|------------------|-----------------|
| Strengthen the task1 skeleton verification beyond directory checks | 0 | It does not block the Round 1 runtime and snippet ABI baseline, but it must be folded into later contract-level tests before claiming the full ELF-first chain | Revisit when expanding tests for generator/build artifacts |
| Flesh out README and Makefile placeholders (`build`, `run`, `list-snippets`, `clean`) | 0 | Documentation and convenience targets do not block the runtime baseline | Revisit while wiring the host-side generator and top-level build flow |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC-4 | task1: Create `snippetgen-demo/` skeleton with top-level `Makefile`, `README.md`, and empty runtime/snippets/generator/suites directories | 0 | 0 | Codex re-ran `python3 -m unittest tests/test_repo_layout.py` and `make test-layout`, both of which passed on the reviewed tree |
| AC-3 | task2: Implement minimal runtime headers and source stubs for env, CSR, trap, timer, finish helpers | 1 | 1 | Codex re-ran `python3 -m unittest tests/test_runtime_surface.py`; the suite passed and confirmed the runtime file surface plus the host-side smoke compile/run path |
| AC-2, AC-3 | task3: Define `xsrt_snippet_desc_t` and a helper runner for `init/run/check/fini` calling convention | 1 | 1 | Codex re-ran `python3 -m unittest tests/test_runtime_surface.py`; the suite passed and confirmed the descriptor surface and `xsrt_run_snippet()` call order smoke |
| AC-1, AC-3 | task4: Implement the 5 PoC snippets and their manifests | 2 | pending | `python3 -m unittest tests/test_snippet_loading.py` passed, including real manifest loading and host compilation of all five snippet sources |
| AC-1 | task5: Implement Python data models for `SnippetSpec`, `SuiteSpec`, `ComposePlan`, and `BuildArtifact` | 2 | pending | `python3 -m unittest tests/test_snippet_loading.py` passed, including imports and use of the typed model objects through the loader path |
| AC-1 | task6: Implement `snippet_db.py` to scan manifests, validate required fields, and resolve source file paths | 2 | pending | `python3 -m unittest tests/test_snippet_loading.py` passed, including manifest field validation, unsupported `kind` rejection, and real snippet DB loading |
| AC-1 | task7: Implement `suite_loader.py` to load the PoC suite, validate `sequence` mode, and produce a deterministic plan | 2 | pending | `python3 -m unittest tests/test_snippet_loading.py` passed, including future-only mode rejection, unknown snippet rejection, and deterministic real-plan generation |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|
