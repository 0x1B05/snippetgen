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

### Plan Version: 1 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initialized tracker from `detail-plan.md` and normalized the ACs into four independent checks | Preserve the original scope while making future round reviews easier | No scope change; AC-1 to AC-4 remain intact |
| 0 | Narrowed the active implementation focus to `task1` after RLCR bootstrap completed in the same round | The loop remained on Round 0, so the round needed one concrete mainline coding objective | No scope change; only execution focus moved to the first planned task |

#### Active Tasks
<!-- Mainline tasks only: each task must directly advance the current round objective and carry routing metadata -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| task1: Create `snippetgen-demo/` skeleton with top-level `Makefile`, `README.md`, and empty runtime/snippets/generator/suites directories | AC-4 | completed_pending_verification | coding | claude | Verified locally with `python3 -m unittest tests/test_repo_layout.py` and `make test-layout` |
| task2: Implement minimal runtime headers and source stubs for env, CSR, trap, timer, finish helpers | AC-3 | pending | coding | claude | Depends on task1 |
| task3: Define `xsrt_snippet_desc_t` and a helper runner for `init/run/check/fini` calling convention | AC-2, AC-3 | pending | coding | claude | Depends on task2 |
| task4: Implement the 5 PoC snippets and their manifests | AC-1, AC-3 | pending | coding | claude | Keep snippet set minimal |
| task5: Implement Python data models for `SnippetSpec`, `SuiteSpec`, `ComposePlan`, and `BuildArtifact` | AC-1 | pending | coding | claude | Host-side model layer |
| task6: Implement `snippet_db.py` to scan manifests, validate required fields, and resolve source file paths | AC-1 | pending | coding | claude | Depends on task5 |
| task7: Implement `suite_loader.py` to load the PoC suite, validate `sequence` mode, and produce a deterministic plan | AC-1 | pending | coding | claude | Depends on task5 |
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
| None | - | - | - |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC-4 | task1: Create `snippetgen-demo/` skeleton with top-level `Makefile`, `README.md`, and empty runtime/snippets/generator/suites directories | 0 | pending | `python3 -m unittest tests/test_repo_layout.py` and `make test-layout` both passed after the skeleton was created |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|
