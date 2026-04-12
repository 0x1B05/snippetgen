.PHONY: build run list-snippets dump-plan test-layout test-snippet-loading repro-vsetvl repro-split-store

build:
	python3 generator/cli.py build suites/scalar_load_legality_poc.yaml

run:
	python3 generator/cli.py run suites/scalar_load_legality_poc.yaml --seed 4660

repro-vsetvl:
	bash -lc 'if [ -n "$$SNIPPETGEN_XS_ENV_SH" ]; then source "$$SNIPPETGEN_XS_ENV_SH"; fi; python3 generator/cli.py run suites/vsetvl_interrupt_search_poc.yaml --seed 4658 --batch-id repro_vsetvl_4658'

repro-split-store:
	bash -lc 'if [ -n "$$SNIPPETGEN_XS_ENV_SH" ]; then source "$$SNIPPETGEN_XS_ENV_SH"; fi; SNIPPETGEN_RUN_MAX_CYCLES=12000 SNIPPETGEN_RUN_MAX_INSTR=12000 python3 generator/cli.py run suites/misaligned_split_store_search_poc.yaml --seed 0 --batch-id repro_split_0 --timeout-sec 140'

list-snippets:
	python3 generator/cli.py list-snippets

dump-plan:
	python3 generator/cli.py dump-plan suites/scalar_load_legality_poc.yaml

test-layout:
	python3 -m unittest tests/test_repo_layout.py

test-snippet-loading:
	python3 -m unittest tests/test_snippet_loading.py
