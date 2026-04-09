# Round 4 Contract

- Mainline Objective: Finish the remaining build-path contract fixes by making the no-arg CLI build entrypoint work, recording full link provenance in `build_manifest.json`, and ensuring failed rebuilds cannot leave stale success artifacts behind.
- Target ACs: AC-4, AC-2
- Blocking Side Issues In Scope: Only issues that prevent the default build entrypoint from succeeding, prevent `build_manifest.json` from recording distinct link provenance, or allow failed rebuilds to preserve stale `test.elf`, `test.bin`, or `build_manifest.json`.
- Queued Side Issues Out of Scope: README/Makefile polish beyond the build entrypoint, `make run`, and any new feature work outside the reviewed build-path contract.
- Success Criteria: `python3 generator/cli.py build` succeeds without an explicit suite path, `build_manifest.json` records a distinct `commands.link`, failed rebuild regression tests prove stale outputs are cleaned up, and the round summary captures fresh combined verification evidence before the next stop-gate review.
