.PHONY: install test run format clean venv

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
BLACK := $(VENV)/bin/black

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

venv:
	python3 -m venv $(VENV)

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) -m src.app

format:
	$(BLACK) src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(VENV)
