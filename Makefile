PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install run run-debug run-app check clean

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

run-debug:
	DEBUG=true $(PYTHON) main.py

run-app:
	$(PYTHON) desktop_app.py

check:
	$(PYTHON) -m py_compile main.py desktop_app.py src/*.py

clean:
	rm -rf __pycache__ src/__pycache__
