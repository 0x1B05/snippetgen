# Changelog

## 2026-04-11

### Added

- Real `run` pipeline with:
  - `--seed`
  - `--seeds`
  - `--seed-range`
  - `--batch-id`
- Batch-scoped run artifact layout under `build/<suite>/runs/<batch_id>/seed_<N>/`
- Structured `batch_meta.json` and per-seed `run_meta.json`
- `disasm` artifact beside every built `test.elf`
- Real XiangShan `emu` adapter
- LightSSS-aware abort workflow for external XiangShan integration
- RISC-V-only runtime/snippet surface
- Runtime-level vector enable in `_start`
- Periodic timer mode for `vsetvl` interrupt search
- `X1/X2/X4/X8` `vsetvl` macro bundles for the search workload

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
- `vsetvl_interrupt_search_poc` can reproduce a ROB assertion on a pre-fix XiangShan tree through the repository common path using:
  - `python3 generator/cli.py run suites/vsetvl_interrupt_search_poc.yaml --seed 4658 --batch-id repro_4658_default`

### Documentation

- `README.md` rewritten as the main human/agent entry point
- XiangShan `emu` usage guide updated
- Release notes added
- Temporary plans and drafts archived under `docs/archive/`

For a fuller release snapshot, see:

- [`docs/release-notes-2026-04-11.md`](docs/release-notes-2026-04-11.md)
