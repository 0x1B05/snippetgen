# Round 5 Contract

- Mainline Objective: Resolve the three Round 5 code-review findings by deduplicating compiled snippet sources, declaring the PyYAML runtime dependency, and rejecting unsupported snippet languages during manifest loading.
- Target ACs: AC-1, AC-4
- Blocking Side Issues In Scope: Only the review findings in `round-5-review-result.md` that block review acceptance: duplicate source compilation causing duplicate definitions, undeclared PyYAML dependency, and unsupported `lang` values slipping past manifest loading.
- Queued Side Issues Out of Scope: The previously queued same-suite concurrent-build race, README/Makefile polish, and any further feature work outside the three review findings.
- Success Criteria: Regression tests fail before the fixes and pass afterward, the dependency is declared in-repo, the loader rejects unsupported languages at load time, duplicate snippet/source references no longer cause duplicate-definition build failures, and Round 5 has a summary plus commit ready for another code-review pass.
