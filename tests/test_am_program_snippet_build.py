from pathlib import Path
import importlib
import json
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AMProgramSnippetBuildTest(unittest.TestCase):
    def test_am_program_sample_uses_ioe_timer_and_serial_paths(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "am_hello_main.c").read_text()

        self.assertIn("xsam_ioe_init()", sample)
        self.assertIn("xsam_dev_timer_uptime_t uptime", sample)
        self.assertIn("xsam_dev_serial_send_t serial", sample)
        self.assertIn("xsam_io_read(XSAM_DEV_TIMER, XSAM_DEVREG_TIMER_UPTIME, &uptime, sizeof(uptime))", sample)
        self.assertIn("xsam_io_write(XSAM_DEV_SERIAL, XSAM_DEVREG_SERIAL_SEND, &serial, sizeof(serial))", sample)

    def test_am_timer_program_waits_for_timer_progress_before_declaring_timeout(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "am_timer_event_main.c").read_text()

        self.assertIn("uint64_t last_time", sample)
        self.assertIn("uint64_t last_compare", sample)
        self.assertIn("xsrt_timer_read_uptime()", sample)
        self.assertIn("xsrt_timer_read_compare()", sample)
        self.assertIn("if (last_time < last_compare)", sample)

    def test_nexus_memscan_program_uses_pmp_and_mprv_for_fault_probe(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_access_fault_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPP_S", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPRV", sample)
        self.assertIn("NEXUS_MEMSCAN_CAUSE_STORE_ACCESS", sample)
        self.assertIn('csrw pmpaddr15, %0', sample)
        self.assertIn('csrw pmpcfg2, %0', sample)
        self.assertIn('csrw pmpaddr1, %0', sample)
        self.assertIn('csrw pmpcfg0, %0', sample)
        self.assertIn('csrrw t0, mstatus, %2', sample)
        self.assertIn('csrw mstatus, t0', sample)
        self.assertIn("static void nexus_memscan_faulting_store(uintptr_t addr)", sample)
        self.assertIn('sd zero, 0(%0)', sample)

    def test_nexus_memscan_fetch_program_uses_locked_pmp_and_resume_epc(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_fetch_fault_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_CAUSE_FETCH_ACCESS", sample)
        self.assertIn("NEXUS_MEMSCAN_PMP_LOCK", sample)
        self.assertIn("static volatile uintptr_t nexus_memscan_fetch_resume_pc", sample)
        self.assertIn('csrw pmpcfg0, %0', sample)
        self.assertIn("frame->epc = nexus_memscan_fetch_resume_pc;", sample)
        self.assertIn("nexus_memscan_trigger_fetch_fault(", sample)
        self.assertIn("la t0, 1f", sample)
        self.assertIn('sd t0, %0', sample)
        self.assertIn('jr %1', sample)

    def test_nexus_memscan_page_fault_program_uses_sv39_satp_and_mprv_probes(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_page_fault_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_CAUSE_LOAD_PAGE", sample)
        self.assertIn("NEXUS_MEMSCAN_CAUSE_STORE_PAGE", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPP_S", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPRV", sample)
        self.assertIn("NEXUS_MEMSCAN_SATP_MODE_SV39", sample)
        self.assertIn("__attribute__((aligned(4096)))", sample)
        self.assertIn('csrw pmpaddr15, %0', sample)
        self.assertIn('csrw pmpcfg2, %0', sample)
        self.assertIn("static void nexus_memscan_install_sv39_root(void)", sample)
        self.assertIn('csrw satp, %0', sample)
        self.assertIn('sfence.vma x0, x0', sample)
        self.assertIn("static void nexus_memscan_faulting_store(uintptr_t addr, uint64_t value)", sample)
        self.assertIn("static uint64_t nexus_memscan_faulting_load(uintptr_t addr)", sample)
        self.assertIn('csrrw t0, mstatus, %2', sample)
        self.assertIn("frame->epc += nexus_memscan_insn_len(frame->epc);", sample)

    def test_nexus_memscan_hugepage_program_uses_level1_leaf_mapping(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_hugepage_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_CAUSE_STORE_PAGE", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPP_S", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPRV", sample)
        self.assertIn("__attribute__((aligned(2097152)))", sample)
        self.assertIn('csrw pmpaddr15, %0', sample)
        self.assertIn('csrw pmpcfg2, %0', sample)
        self.assertIn("static void nexus_memscan_map_huge_leaf(", sample)
        self.assertIn("static uint64_t nexus_memscan_faulting_load(uintptr_t addr)", sample)
        self.assertIn("static void nexus_memscan_faulting_store(uintptr_t addr, uint64_t value)", sample)
        self.assertIn("frame->epc += nexus_memscan_insn_len(frame->epc);", sample)

    def test_nexus_memscan_hugepage_access_fault_program_uses_huge_leaf_and_pmp_deny_window(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_hugepage_access_fault_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_CAUSE_LOAD_ACCESS", sample)
        self.assertIn("NEXUS_MEMSCAN_CAUSE_STORE_ACCESS", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPP_S", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPRV", sample)
        self.assertIn("__attribute__((aligned(2097152)))", sample)
        self.assertIn('csrw pmpaddr15, %0', sample)
        self.assertIn('csrw pmpcfg2, %0', sample)
        self.assertIn('csrw pmpaddr1, %0', sample)
        self.assertIn('csrw pmpcfg0, %0', sample)
        self.assertIn("static void nexus_memscan_map_huge_leaf(", sample)
        self.assertIn("static uint64_t nexus_memscan_faulting_load(uintptr_t addr)", sample)
        self.assertIn("static void nexus_memscan_faulting_store(uintptr_t addr, uint64_t value)", sample)
        self.assertIn("frame->epc += nexus_memscan_insn_len(frame->epc);", sample)

    def test_nexus_memscan_hugepage_atom_fault_program_uses_amo_lr_and_huge_leafs(self) -> None:
        sample = (ROOT / "snippets" / "programs" / "nexus_memscan_hugepage_atom_fault_main.c").read_text()

        self.assertIn("NEXUS_MEMSCAN_CAUSE_LOAD_PAGE", sample)
        self.assertIn("NEXUS_MEMSCAN_CAUSE_STORE_PAGE", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPP_S", sample)
        self.assertIn("NEXUS_MEMSCAN_MSTATUS_MPRV", sample)
        self.assertIn("__attribute__((aligned(2097152)))", sample)
        self.assertIn('csrw pmpaddr15, %0', sample)
        self.assertIn('csrw pmpcfg2, %0', sample)
        self.assertIn("static void nexus_memscan_map_huge_leaf(", sample)
        self.assertIn("static void nexus_memscan_faulting_amoadd(uintptr_t addr, uint64_t value)", sample)
        self.assertIn("static uint64_t nexus_memscan_faulting_lr(uintptr_t addr)", sample)
        self.assertIn("amoadd.d", sample)
        self.assertIn("lr.d", sample)
        self.assertIn("frame->epc += nexus_memscan_insn_len(frame->epc);", sample)

    def test_emitter_wraps_main_style_program_as_snippet(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        model = importlib.import_module("generator.xsgen.model")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            program_source = Path(tmpdir) / "demo_program.c"
            program_source.write_text("int main(void) { return 0; }\n")

            init_source = ROOT / "snippets" / "core" / "init_basic_env.c"
            finish_source = ROOT / "snippets" / "core" / "finish_check.c"

            plan = model.ComposePlan(
                suite_name="am_program_emit_case",
                target="xiangshan-verilator",
                seed=7,
                snippet_ids=("init_basic_env", "demo_program", "finish_check"),
                snippets=(
                    model.SnippetSpec(
                        id="init_basic_env",
                        kind="proc",
                        lang="c",
                        sources=(init_source.resolve(),),
                    ),
                    model.SnippetSpec(
                        id="demo_program",
                        kind="am_program",
                        lang="c",
                        entry="main",
                        sources=(program_source.resolve(),),
                    ),
                    model.SnippetSpec(
                        id="finish_check",
                        kind="proc",
                        lang="c",
                        sources=(finish_source.resolve(),),
                    ),
                ),
            )
            artifact = toolchain.artifact_paths_for_suite(Path(tmpdir), plan.suite_name)

            emitter.emit_harness(plan, artifact.generated_suite_path)
            harness = artifact.generated_suite_path.read_text()

            self.assertIn('#include "xsam/program_snippet.h"', harness)
            self.assertIn("#define main xsam_program_entry_demo_program", harness)
            self.assertIn(f'#include "{program_source.resolve()}"', harness)
            self.assertIn("#undef main", harness)
            self.assertIn(
                'XSAM_DEFINE_PROGRAM_SNIPPET(snippet_demo_program, "demo_program", xsam_program_entry_demo_program)',
                harness,
            )
            self.assertIn("xsrt_run_snippet(&env, &snippet_init_basic_env);", harness)
            self.assertIn("xsrt_run_snippet(&env, &snippet_demo_program);", harness)
            self.assertIn("xsrt_run_snippet(&env, &snippet_finish_check);", harness)

    def test_build_pipeline_compiles_am_program_via_generated_harness(self) -> None:
        emitter = importlib.import_module("generator.xsgen.emitter")
        model = importlib.import_module("generator.xsgen.model")
        toolchain = importlib.import_module("generator.xsgen.toolchain")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            program_source = tmp_root / "demo_program.c"
            helper_source = tmp_root / "demo_helper.c"
            program_source.write_text(
                "\n".join(
                    [
                        "extern int demo_helper(void);",
                        "int main(void) {",
                        "  return demo_helper();",
                        "}",
                    ]
                )
                + "\n"
            )
            helper_source.write_text("int demo_helper(void) { return 0; }\n")

            plan = model.ComposePlan(
                suite_name="am_program_build_case",
                target="xiangshan-verilator",
                seed=11,
                snippet_ids=("init_basic_env", "demo_program", "finish_check"),
                snippets=(
                    model.SnippetSpec(
                        id="init_basic_env",
                        kind="proc",
                        lang="c",
                        sources=((ROOT / "snippets" / "core" / "init_basic_env.c").resolve(),),
                    ),
                    model.SnippetSpec(
                        id="demo_program",
                        kind="am_program",
                        lang="c",
                        entry="main",
                        sources=(program_source.resolve(), helper_source.resolve()),
                    ),
                    model.SnippetSpec(
                        id="finish_check",
                        kind="proc",
                        lang="c",
                        sources=((ROOT / "snippets" / "core" / "finish_check.c").resolve(),),
                    ),
                ),
            )
            artifact = toolchain.artifact_paths_for_suite(tmp_root, plan.suite_name)

            emitter.emit_harness(plan, artifact.generated_suite_path)
            toolchain.build_artifacts(ROOT, plan, artifact)

            self.assertTrue(artifact.elf_path.is_file())
            self.assertTrue(artifact.bin_path.is_file())
            self.assertTrue(artifact.build_manifest_path.is_file())

            manifest = json.loads(artifact.build_manifest_path.read_text())
            compile_sources = [
                cmd[cmd.index("-c") + 1]
                for cmd in manifest["commands"]["compile"]
            ]
            self.assertNotIn(str(program_source.resolve()), compile_sources)
            self.assertIn(str(helper_source.resolve()), compile_sources)
            self.assertIn(str(artifact.generated_suite_path), compile_sources)
            self.assertIn(
                str((ROOT / "runtime" / "src" / "xsam_program_snippet.c").resolve()),
                compile_sources,
            )


if __name__ == "__main__":
    unittest.main()
