PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install run run-debug check clean

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

run-debug:
	DEBUG=true $(PYTHON) main.py

check:
	$(PYTHON) -m py_compile main.py src/*.py

clean:
	rm -rf __pycache__ src/__pycache__
