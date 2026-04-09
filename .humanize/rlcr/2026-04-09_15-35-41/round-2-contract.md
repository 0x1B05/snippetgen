# Round 2 Contract

- Mainline Objective: Implement the five PoC snippets plus the deterministic host-side model and loading layer so the repository can resolve manifests and a sequence suite into a concrete ordered plan.
- Target ACs: AC-1, AC-3
- Blocking Side Issues In Scope: Only issues that prevent adding snippet source/manifests, building the manifest database, loading the PoC suite, or producing a deterministic ordered plan from that suite.
- Queued Side Issues Out of Scope: Harness emission, toolchain integration, actual `ELF/bin/build_manifest.json` artifacts, and README/Makefile polish beyond removing misleading behavior if it directly interferes with this round's mainline objective.
- Success Criteria: The five snippet source files and manifests exist, `generator/cli.py`, `generator/xsgen/model.py`, `generator/xsgen/snippet_db.py`, and `generator/xsgen/suite_loader.py` exist, new loader/plan tests fail before implementation and pass afterward, and the round summary records that AC-1 and AC-3 advanced without claiming end-to-end build completion.
