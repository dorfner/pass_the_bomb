.PHONY: install test run format clean venv

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
BLACK := $(VENV)/bin/black

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install .

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) -m src.app

format:
	$(BLACK) src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(VENV)
