.PHONY: build run list-snippets dump-plan test-layout test-snippet-loading

build:
	python3 generator/cli.py build suites/scalar_load_legality_poc.yaml

run:
	python3 generator/cli.py run suites/scalar_load_legality_poc.yaml --seed 4660

list-snippets:
	python3 generator/cli.py list-snippets

dump-plan:
	python3 generator/cli.py dump-plan suites/scalar_load_legality_poc.yaml

test-layout:
	python3 -m unittest tests/test_repo_layout.py

test-snippet-loading:
	python3 -m unittest tests/test_snippet_loading.py
