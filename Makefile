help:
	@echo "Available make targets:"
	@echo ""
	@echo "  setup         Set up local virtual environment"
	@echo "  test          Run pytest tests"
	@echo "  format        Format source code with black"
	@echo ""

.venv/bin/python3:
	python3 -m venv .venv

.venv/bin/pipenv: .venv/bin/python3
	.venv/bin/pip install pipenv

setup: .venv/bin/pipenv
	PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv install --dev
	.venv/bin/pip install -e .

.PHONY: test
test: .venv/bin/pipenv .venv/bin/pytest
	.venv/bin/pytest \
		--cov=. \
		--cov-report term \
		--cov-report term-missing \
		${PYTEST_ARGS} -v tests

format: .venv/bin/pipenv .venv/bin/black
	.venv/bin/pipenv run black .

lint: .venv/bin/pipenv .venv/bin/flake8
	.venv/bin/pipenv run flake8 *.py tests churchtools postfix_sync

.PHONY: sync_postfix
sync_postfix: .venv/bin/pipenv
	@PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv --bare install 1>/dev/null 2>&1
	@.venv/bin/pip install -e . 1>/dev/null 2>&1
	@.venv/bin/pipenv --bare run python syncPostfixAliases.py