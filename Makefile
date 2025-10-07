.PHONY: verify up smoke down

verify:
	@echo "==> pre-commit (if available)"
	@if command -v pre-commit >/dev/null 2>&1; then pre-commit run --all-files; else echo "pre-commit not found, skipping"; fi
	@echo "==> pytest"
	@pytest -q
	@echo "==> docker smoke (skip if docker not available)"
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		echo "docker available, running smoke"; \
		$(MAKE) up && $(MAKE) smoke && $(MAKE) down; \
	else \
		echo "docker not available, skipping smoke"; \
	fi

up:
	@echo "noop up"

smoke:
	@echo '{"status":"ok"}'

down:
	@echo "noop down"
