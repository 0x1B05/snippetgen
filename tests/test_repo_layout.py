from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "Makefile",
    "README.md",
]

REQUIRED_DIRECTORIES = [
    "runtime",
    "runtime/include",
    "runtime/src",
    "runtime/arch/riscv64",
    "runtime/platform/xiangshan",
    "snippets",
    "snippets/include",
    "snippets/manifests",
    "snippets/core",
    "snippets/scalar_load_legality",
    "generator",
    "generator/xsgen",
    "suites",
    "build",
    "tests",
]


class RepoLayoutTest(unittest.TestCase):
    def test_required_top_level_files_exist(self) -> None:
        for relative_path in REQUIRED_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_required_directories_exist(self) -> None:
        for relative_path in REQUIRED_DIRECTORIES:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_dir())


if __name__ == "__main__":
    unittest.main()
