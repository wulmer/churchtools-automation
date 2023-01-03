PYTHON=python3.9

help:
	@echo "Available make targets:"
	@echo ""
	@echo "  setup              Set up local virtual environment"
	@echo "  test               Run pytest tests"
	@echo "  test-our-ct-setup  Test our CT configuration"
	@echo "  format             Format source code with black"
	@echo "  lint               Run flake8"
	@echo "  check_godiplan     Run the script for checking the GoDi plan"
	@echo "  check_ldap         Run the script for checking the LDAP settings"
	@echo "  archive_godiplan   Run the script for archiving old GoDi plan entries"
	@echo "  sync_postfix       Run the script for synching a Postfix virtual alias file"
	@echo "  sync_mitarbeiter   Run the script for synching MA status and All-MA group"
	@echo ""

.venv/bin/${PYTHON}:
	${PYTHON} -m venv .venv

.venv/bin/pipenv: .venv/bin/${PYTHON}
	@.venv/bin/pip install pipenv -qq

setup: .venv_is_uptodate

.venv_is_uptodate: .venv/bin/pipenv Pipfile.lock
	PIPENV_VENV_IN_PROJECT=1 .venv/bin/pipenv --bare install --dev
	.venv/bin/${PYTHON} -m pip install -qq -e .
	.venv/bin/${PYTHON} -m pip install -qq -e postfix_sync/src
	touch .venv_is_uptodate

Pipfile.lock: Pipfile
	.venv/bin/pipenv lock

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

.PHONY: test-our-ct-setup
test-our-ct-setup: .venv/bin/pipenv .venv/bin/pytest
	@.venv/bin/pytest \
		${PYTEST_ARGS} -v our_churchtools_setup/tests

.PHONY: format
format: .venv/bin/pipenv .venv/bin/black
	@.venv/bin/pipenv run black .

.PHONY: lint
lint: .venv/bin/pipenv .venv/bin/flake8
	@.venv/bin/pipenv run flake8 *.py tests churchtools postfix_sync

.PHONY: sync_postfix
sync_postfix: .venv_is_uptodate
	@.venv/bin/pipenv --bare run ${PYTHON} syncPostfixAliases.py

.PHONY: sync_mitarbeiter
sync_mitarbeiter: .venv_is_uptodate
	@.venv/bin/pipenv --bare run ${PYTHON} syncMitarbeiterStatus.py
	@.venv/bin/pipenv --bare run ${PYTHON} syncAlleMitarbeiter.py

.PHONY: archive_godiplan
archive_godiplan: .venv_is_uptodate
	@.venv/bin/pipenv --bare run python archiveGodiPlan.py

.PHONY: check_godiplan
check_godiplan: .venv_is_uptodate
	@.venv/bin/pipenv --bare run python checkGodiPlan.py

.PHONY: check_old_godi_folders
check_old_godi_folders: .venv_is_uptodate
	@.venv/bin/pipenv --bare run python checkOldGoDiFolders.py

.PHONY: check_ldap
check_ldap: .venv_is_uptodate
	@.venv/bin/pipenv --bare run python checkLDAP.py

clean:
	rm -rf .venv
	find . -name __pycache__ -type d -exec rm -rf \{\} \;
