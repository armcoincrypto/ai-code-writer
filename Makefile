.PHONY: up logs smoke down rebuild clean
PORT ?= 8000

up:
	DOCKER_BUILDKIT=1 docker compose up -d --build

logs:
	docker compose logs -f

smoke:
	@echo "→ /health"
	@curl -sf --retry 10 --retry-delay 1 --retry-connrefused --retry-all-errors http://127.0.0.1:8000/health && echo
	@echo "→ /sum?a=2&b=3"
	@curl -sf --retry 10 --retry-delay 1 --retry-connrefused --retry-all-errors "http://127.0.0.1:8000/sum?a=2&b=3" && echo

down:
	docker compose down

rebuild:
	DOCKER_BUILDKIT=1 docker compose build --no-cache
	docker compose up -d

clean:
	- docker stop $$(docker ps -q --filter publish=$(PORT)) 2>/dev/null || true
	- docker system prune -f
