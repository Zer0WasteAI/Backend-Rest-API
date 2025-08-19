PYTHON ?= python3

.PHONY: test unit integration functional all test-all ci

unit:
	$(PYTHON) scripts/test_all.py --scope unit --no-docker-check

integration:
	$(PYTHON) scripts/test_all.py --scope integration --auto-up

functional:
	$(PYTHON) scripts/test_all.py --scope functional --auto-up

test:
	$(PYTHON) scripts/test_all.py --auto-up -n 4

test-all:
	$(PYTHON) scripts/run_all_tests.py --auto-up -n 4 --stop-on-failure

ci:
	$(PYTHON) scripts/run_all_tests.py --auto-up -n 4 --no-coverage --stop-on-failure

