# Round 1 Contract

- Mainline Objective: Establish the minimal runtime baseline and snippet ABI needed for the ELF-first PoC by implementing `task2` and the directly dependent `task3`.
- Target ACs: AC-2, AC-3
- Blocking Side Issues In Scope: Only issues that prevent defining the runtime interface surface, the snippet descriptor ABI, or the helper runner in a testable form.
- Queued Side Issues Out of Scope: Stronger task1 skeleton verification, README/Makefile polish, host-side generator modules, suite YAML, snippet manifests, and any end-to-end `ELF/bin` build work beyond the runtime and ABI baseline.
- Success Criteria: Round 1 adds the required runtime headers/source stubs and `xsrt_snippet_desc_t`/runner interface, the new tests fail before those files exist and pass after implementation, and the round summary records the evidence without claiming the whole PoC is done.
