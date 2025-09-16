# ---- Config ----
OAI_BASE ?= http://127.0.0.1:11434/v1
OAI_KEY  ?= ollama
MODEL    ?= llama3.2
PY       := ./.venv/bin/python3

export OPENAI_BASE_URL := $(OAI_BASE)
export OPENAI_API_KEY  := $(OAI_KEY)

.PHONY: deps fmt lint typecheck test verify gen gen-run gen-test gen-fastapi

# ---- Toolchain ----
deps:
	$(PY) -m pip install --upgrade pip
	if [ -f requirements.txt ]; then $(PY) -m pip install -r requirements.txt; fi
	$(PY) -m pip install -r requirements-dev.txt

fmt:
	$(PY) -m isort .
	$(PY) -m black .

lint:
	$(PY) -m flake8 .

typecheck:
	$(PY) -m mypy .

test:
	$(PY) -m pytest

verify: fmt lint typecheck test
	@echo "✅ verify complete"

# ---- Generators ----
# Usage: make gen TASK="print('hello')" OUT=hello.py
gen:
	$(PY) code_writer.py --provider openai --model $(MODEL) \
	  --task "$(TASK)" --out "$(OUT)" --format --syntax-check

# Usage: make gen-run TASK="build a CLI add two ints --a and --b and print sum" OUT=add_cli.py ARGS="--a 2 --b 5"
gen-run:
	$(PY) code_writer.py --provider openai --model $(MODEL) \
	  --task "$(TASK)" --out "$(OUT)" --format --syntax-check
	$(PY) "$(OUT)" $(ARGS)
	@echo "✅ Generated and executed $(OUT)"

# Usage: make gen-test TASK="print('UNIT TEST OK')" OUT=unit_ok.py EXPECT="UNIT TEST OK"
gen-test:
	$(PY) code_writer.py --provider openai --model $(MODEL) \
	  --task "$(TASK)" --out "$(OUT)" --with-tests --expect-output "$(EXPECT)" \
	  --format --run-tests --verbose
	@echo "✅ Generated, formatted, and tested $(OUT)"

# Usage: make gen-fastapi
gen-fastapi:
	$(PY) code_writer.py --provider openai --model $(MODEL) \
	  --domain fastapi --task "simple API with /debug route" \
	  --out app.py --requirements --install-deps --format --syntax-check
	@echo "🚀 Run: ./.venv/bin/python3 app.py"

.PHONY: doctor
doctor:
	./.venv/bin/python3 dev_doctor.py --full

.PHONY: doctor-verify
doctor-verify:
	./.venv/bin/python3 dev_doctor.py --full --run-verify

.PHONY: checksum
checksum:
	./.venv/bin/python3 checksum_cli.py --help

.PHONY: fmt-auto
fmt-auto:
	./.venv/bin/python3 -m isort .
	./.venv/bin/python3 -m black .
	./.venv/bin/autoflake --remove-all-unused-imports --remove-unused-variables -i $(shell git ls-files '*.py')
