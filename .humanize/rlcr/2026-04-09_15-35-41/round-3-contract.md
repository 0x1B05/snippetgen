# Round 3 Contract

- Mainline Objective: Finish the first-stage PoC build chain by completing the remaining loader rejection contracts plus the emitter, toolchain, and artifact-producing build path.
- Target ACs: AC-2, AC-4
- Blocking Side Issues In Scope: Only issues that prevent matching the required `future-only` or `not implemented in ELF-first PoC` rejection text, emitting `generated_suite.c`, compiling and linking the runtime/snippet/harness set into `test.elf`, converting it to `test.bin`, or writing `build_manifest.json`.
- Queued Side Issues Out of Scope: README polish, `make run`, deeper target-side boot or trap behavior, and the final analyze pass in `task12` before build artifacts exist.
- Success Criteria: Round 3 makes `generator/cli.py build` and `make build` generate `build/scalar_load_legality_poc/generated_suite.c`, `test.elf`, `test.bin`, and `build_manifest.json`; the new tests fail before implementation and pass afterward; and the summary records fresh evidence for AC-2 and AC-4 without claiming the final analyze pass is done.
