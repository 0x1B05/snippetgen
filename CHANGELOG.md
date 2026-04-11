# Changelog

## 2026-04-11

### Added

- Real `run` pipeline with:
  - `--seed`
  - `--seeds`
  - `--seed-range`
- Stable run artifact layout under `build/<suite>/runs/seed_<N>/`
- Structured `run_ledger.json` and per-seed `run_meta.json`
- `disasm` artifact beside every built `test.elf`
- Real XiangShan `emu` adapter
- LightSSS-aware abort workflow for external XiangShan integration

### New Suites

- `scalar_load_legality_poc`
- `vsetvl_interrupt_path_poc`
- `interrupt_response_poc`
- `vsetvl_interrupt_search_poc`
- `misaligned_split_store_search_poc`

### Notable Outcomes

- Real timer interrupt response is now observable in a dedicated suite
- Path-oriented `vsetvl` workloads can be built and run end to end
- The misaligned split-store search workload can reproduce an `abort` path on a pre-fix XiangShan tree

### Documentation

- `README.md` rewritten as the main human/agent entry point
- XiangShan `emu` usage guide updated
- Release notes added
- Temporary plans and drafts archived under `docs/archive/`

For a fuller release snapshot, see:

- [`docs/release-notes-2026-04-11.md`](/home/dfpmts/XS/framework/snippetgen-demo/docs/release-notes-2026-04-11.md)
