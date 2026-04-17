# Docs Index

This directory is split into three kinds of material:

## Start Here

- [`../README.md`](../README.md)
  - repository overview, quick start, suite map, agent entry points
- [`2026-04-10-xiangshan-emu-workload-howto.md`](2026-04-10-xiangshan-emu-workload-howto.md)
  - build and run workloads on XiangShan `emu`
- [`release-notes-2026-04-11.md`](release-notes-2026-04-11.md)
  - current release snapshot

## Investigation Notes

- [`2026-04-10-vsetvl-hang-investigation-notes.md`](2026-04-10-vsetvl-hang-investigation-notes.md)
  - `vsetvl` and interrupt investigation trail
- [`2026-04-13-prefetchw-difftest-investigation-notes.md`](2026-04-13-prefetchw-difftest-investigation-notes.md)
  - `prefetch.w`, `M_PFW`, delayed `tl_denied`, and NEMU difftest investigation trail

## Archived Plans And Drafts

- [`archive/README.md`](archive/README.md)
  - archived requirements, plans, and drafts

## Intended Reading Order For Agents

1. [`../README.md`](../README.md)
2. target suite in `suites/`
3. snippet manifests in `snippets/manifests/`
4. snippet sources in `snippets/`
5. generator pipeline in `generator/xsgen/`
6. tests in `tests/`
