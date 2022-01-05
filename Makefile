PYTHON=python3.8

help:
	@echo "Available make targets:"
	@echo ""
	@echo "  setup              Set up local virtual environment"
	@echo "  test               Run pytest tests"
	@echo "  test-our-ct-setup  Test our CT configuration"
	@echo "  format             Format source code with black"
	@echo "  lint               Run flake8"
	@echo "  sync_postfix       Run the script for synching a Postfix virtual alias file"
	@echo "  sync_mitarbeiter   Run the script for synching MA status and All-MA group"
	@echo ""

.venv/bin/${PYTHON}:
	${PYTHON} -m venv .venv

.venv/bin/pipenv: .venv/bin/${PYTHON}
	.venv/bin/pip install pipenv

setup: .venv_is_uptodate

.venv_is_uptodate: .venv/bin/pipenv Pipfile.lock
	PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv install --dev
	.venv/bin/pip install -e .
	.venv/bin/pip install -e postfix_sync/src
	touch .venv_is_uptodate

.venv/bin/pytest: .venv_is_uptodate

.venv/bin/black: .venv_is_uptodate

.PHONY: test
test: .venv/bin/pipenv .venv/bin/pytest
	rm -rf htmlcov
	.venv/bin/pytest \
		--cov=. \
		--cov-report html \
		--cov-report term \
		--cov-report term-missing \
		${PYTEST_ARGS} -v postfix_sync/tests

test-our-ct-setup: .venv/bin/pipenv .venv/bin/pytest
	.venv/bin/pytest \
		${PYTEST_ARGS} -v our_churchtools_setup/tests

format: .venv/bin/pipenv .venv/bin/black
	.venv/bin/pipenv run black .

lint: .venv/bin/pipenv .venv/bin/flake8
	.venv/bin/pipenv run flake8 *.py tests churchtools postfix_sync

.PHONY: sync_postfix
sync_postfix: .venv/bin/pipenv
	@PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv --bare install 1>/dev/null 2>&1
	@.venv/bin/pip install -e . 1>/dev/null 2>&1
	@.venv/bin/pip install -e postfix_sync/src 1>/dev/null 2>&1
	@.venv/bin/pipenv --bare run ${PYTHON} syncPostfixAliases.py

.PHONY: sync_mitarbeiter
sync_mitarbeiter: .venv/bin/pipenv
	@PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv --bare install 1>/dev/null 2>&1
	@.venv/bin/pip install -e . 1>/dev/null 2>&1
	@.venv/bin/pip install -e postfix_sync/src 1>/dev/null 2>&1
	@.venv/bin/pipenv --bare run ${PYTHON} syncMitarbeiterStatus.py
	@.venv/bin/pipenv --bare run ${PYTHON} syncAlleMitarbeiter.py

.PHONY: check_godiplan
check_godiplan: .venv/bin/pipenv
	@PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv --bare install 1>/dev/null 2>&1
	@.venv/bin/pip install -e . 1>/dev/null 2>&1
	@.venv/bin/pipenv --bare run python checkGodiPlan.py

clean:
	rm -rf .venv
	find . -name __pycache__ -type d -exec echo rm -rf \{\} \;
