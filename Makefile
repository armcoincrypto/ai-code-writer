.PHONY: up logs smoke down rebuild clean
PORT ?= 8000

up:
	DOCKER_BUILDKIT=1 docker compose up -d --build

logs:
	docker compose logs -f

smoke:
	@curl -sf http://127.0.0.1:$(PORT)/health && echo
	@curl -sf "http://127.0.0.1:$(PORT)/sum?a=2&b=3" && echo

down:
	docker compose down

rebuild:
	DOCKER_BUILDKIT=1 docker compose build --no-cache
	docker compose up -d

clean:
	- docker stop $$(docker ps -q --filter publish=$(PORT)) 2>/dev/null || true
	- docker system prune -f
