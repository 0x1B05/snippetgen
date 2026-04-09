- [P1] Make `_start` transfer control into `main` — /home/dfpmts/XS/framework/snippetgen-demo/runtime/arch/riscv64/start.S:3-4
  If `test.elf` is ever booted on XiangShan/Verilator, `_start` immediately executes `ret` with no stack setup and no valid return address, so the generated `main()` and every emitted snippet are unreachable. The build still goes green, but the produced ELF is not actually executable as the advertised PoC.

- [P1] Issue a real misaligned load in `unaligned_load` — /home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/unaligned_load.c:16-19
  When this suite runs on the target, these lines only perform four byte loads from an odd address and reassemble the word in software. That never emits a misaligned 32-bit load instruction, so a core with broken misaligned scalar-load handling would still pass `check_scalar_load_legality`, defeating the main purpose of this PoC.

- [P2] Reject non-integer or negative suite seeds — /home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/suite_loader.py:50-50
  `seed` is coerced with `int(...)` here, so malformed YAML such as `seed: -1`, `seed: 1.5`, or `seed: true` is accepted instead of being rejected during suite loading. That either silently rewrites the requested seed or, in the negative case, reaches `emit_harness()` as `0x-1ull` and fails later as a C compile error rather than a clear planning/validation error.
The patch establishes the basic loader/build pipeline, but two core paths are still functionally wrong: the generated ELF cannot execute because `_start` never reaches `main`, and the showcased scalar-load legality suite does not actually perform a misaligned word load. Suite seed validation also allows malformed inputs to slip past loading and fail later in compilation.

Full review comments:

- [P1] Make `_start` transfer control into `main` — /home/dfpmts/XS/framework/snippetgen-demo/runtime/arch/riscv64/start.S:3-4
  If `test.elf` is ever booted on XiangShan/Verilator, `_start` immediately executes `ret` with no stack setup and no valid return address, so the generated `main()` and every emitted snippet are unreachable. The build still goes green, but the produced ELF is not actually executable as the advertised PoC.

- [P1] Issue a real misaligned load in `unaligned_load` — /home/dfpmts/XS/framework/snippetgen-demo/snippets/scalar_load_legality/unaligned_load.c:16-19
  When this suite runs on the target, these lines only perform four byte loads from an odd address and reassemble the word in software. That never emits a misaligned 32-bit load instruction, so a core with broken misaligned scalar-load handling would still pass `check_scalar_load_legality`, defeating the main purpose of this PoC.

- [P2] Reject non-integer or negative suite seeds — /home/dfpmts/XS/framework/snippetgen-demo/generator/xsgen/suite_loader.py:50-50
  `seed` is coerced with `int(...)` here, so malformed YAML such as `seed: -1`, `seed: 1.5`, or `seed: true` is accepted instead of being rejected during suite loading. That either silently rewrites the requested seed or, in the negative case, reaches `emit_harness()` as `0x-1ull` and fails later as a C compile error rather than a clear planning/validation error.
