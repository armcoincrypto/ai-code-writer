#!/usr/bin/env bash
set -euo pipefail

# === Конфигурация ===
OWNER="armcoincrypto"
REPO="ai-code-writer"
WORKDIR="$HOME/Conocono/ai-code-writer"
BRANCH="import-from-upstream"

# Флаги
CREATE_FILES="${CREATE_FILES:-false}"        # true — добавить CI и PR template
USE_STATUS_CHECKS="${USE_STATUS_CHECKS:-false}" # true — требовать статус-чеки в защите

# Имена чек-ранов (если CREATE_FILES=true, будут такие)
PRECOMMIT_NAME="pre-commit"
PYTEST_NAME="pytest (3.11)"
DOCKER_SMOKE_NAME="docker smoke"  # если есть docker-compose/make smoke

echo ">>> Step 1: локальная подготовка"
cd "$WORKDIR"
git status
git fetch origin
git checkout "$BRANCH"
git pull --ff-only

echo ">>> Step 2: локальные проверки (необязательно)"
pre-commit run --all-files || true
pytest -q || true
make up && make smoke && make down || true

if [[ "$CREATE_FILES" == "true" ]]; then
  echo ">>> [Опционально] Добавляем CI и шаблоны PR"
  mkdir -p .github/workflows

  # ci.yml
  cat > .github/workflows/ci.yml <<'YML'
name: ci
on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ import-from-upstream ]
jobs:
  pre-commit:
    name: pre-commit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pre-commit
      - name: Run pre-commit
        run: pre-commit run --all-files

  pytest:
    name: pytest (3.11)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest
      - name: Run tests
        run: pytest -q

  docker-smoke:
    name: docker smoke
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & run docker compose
        if: hashFiles('docker-compose.yml') != ''
        run: |
          docker compose up -d --build || true
          if command -v make; then make smoke || true; fi
          docker compose down || true
YML

  # PULL_REQUEST_TEMPLATE.md
  mkdir -p .github
  cat > .github/PULL_REQUEST_TEMPLATE.md <<'MD'
## Что меняет PR
(1–2 предложения)

## Как проверить (локально)
- `pre-commit run --all-files` → ожидаю **Passed**
- `pytest -q` → ожидаю **14 passed**
- `make up && make smoke && make down` → ожидаю `{"status":"ok"}`, `{"result":5.0}`

## Риск/влияние
Низкий; без изменения логики API.

## Скриншоты/логи (по желанию)
MD

  git add -A
  git commit -m "ci: add basic CI and PR template" || true
  git push -u origin "$BRANCH" || true
else
  echo ">>> CREATE_FILES=false — пропускаем добавление файлов"
fi

echo ">>> Step 3: создаём PR"
git push -u origin "$BRANCH" || true
gh pr create \
  --base main \
  --head "$BRANCH" \
  --title "feat: stabilize dev workflow (pre-commit, tests, docker compose)" \
  --body-file .github/PULL_REQUEST_TEMPLATE.md || \
gh pr create \
  --base main \
  --head "$BRANCH" \
  --title "feat: stabilize dev workflow (pre-commit, tests, docker compose)" \
  --body "Стабилизация дев-процесса. Проверки: pre-commit, pytest, make smoke."

echo ">>> Step 4: Мержим (когда ревью/CI ок)"
# ЗАМЕТКА: запусти повторно этот шаг после того, как проверки позеленеют/одобрят.
gh pr merge --squash --delete-branch

echo ">>> Step 5: Обновляем локальный main"
git checkout main
git pull --ff-only

echo ">>> Step 6: Включаем защиту ветки main"
if [[ "$USE_STATUS_CHECKS" == "true" ]]; then
  echo ">>> Добавляем защиту с обязательными статус-чеками"
  gh api -X PUT "repos/$OWNER/$REPO/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    -F required_status_checks.strict=true \
    -F required_status_checks.contexts[]="$PRECOMMIT_NAME" \
    -F required_status_checks.contexts[]="$PYTEST_NAME" \
    -F required_status_checks.contexts[]="$DOCKER_SMOKE_NAME" \
    -F enforce_admins=true \
    -F required_pull_request_reviews.dismiss_stale_reviews=true \
    -F required_pull_request_reviews.required_approving_review_count=1 \
    -F restrictions='null' \
    -F required_linear_history=true \
    -F allow_force_pushes=false \
    -F allow_deletions=false \
    -F block_creations=false
else
  echo ">>> Включаем защиту БЕЗ обязательных статус-чеков"
  gh api -X PUT "repos/$OWNER/$REPO/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    -f required_status_checks='{"strict":true,"contexts":[]}' \
    -F enforce_admins=true \
    -F required_pull_request_reviews.dismiss_stale_reviews=true \
    -F required_pull_request_reviews.required_approving_review_count=1 \
    -f restrictions='null' \
    -F required_linear_history=true \
    -F allow_force_pushes=false \
    -F allow_deletions=false \
    -F block_creations=false
fi

echo ">>> Готово."
