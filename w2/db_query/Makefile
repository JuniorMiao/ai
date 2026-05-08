# db_query — 常用命令
#
# 用法：在 `w2/db_query` 目录执行 `make <target>`；或在仓库根执行 `make -C w2/db_query <target>`。
# 依赖：GNU Make、uv（后端）、Node/npm（前端）。Windows 可使用 Git Bash 自带的 make。
#
# PowerShell 无 make 时：同目录执行 .\db_query.ps1 <target>（目标名称一致）。
#
.PHONY: help install install-backend install-frontend sync-backend sync dev-backend dev-frontend \
	lint lint-backend lint-frontend test-backend build-frontend clean-backend-cache openapi-json \
	audit-frontend audit-fix-frontend

BACKEND := backend
FRONTEND := frontend
UV := uv
HOST ?= 0.0.0.0
PORT ?= 8000

help:
	@echo "db_query targets:"
	@echo "  install            - 后端 uv sync + 前端 npm install"
	@echo "  install-backend    - uv sync --all-groups（$(BACKEND)）"
	@echo "  install-frontend   - npm install（$(FRONTEND)）"
	@echo "  sync-backend       - 同 install-backend"
	@echo "  dev-backend        - 启动 FastAPI（$(HOST):$(PORT)），需已实现 db_query.main:app"
	@echo "  dev-frontend       - 启动 Vite 开发服务器"
	@echo "  lint / lint-*      - Ruff / ESLint"
	@echo "  test-backend       - pytest"
	@echo "  build-frontend     - tsc + vite build"
	@echo "  openapi-json       - 打印 OpenAPI JSON（需服务已启动；需 curl）"
	@echo "  clean-backend-cache - 删除后端 __pycache__ / .pytest_cache / .ruff_cache"
	@echo "  audit-frontend      - 前端 npm audit（须在 frontend 目录有 lockfile）"
	@echo "  audit-fix-frontend  - 前端 npm audit fix（不加 --force）"

install: install-backend install-frontend

install-backend sync-backend sync:
	cd $(BACKEND) && $(UV) sync --all-groups

install-frontend:
	cd $(FRONTEND) && npm install

dev-backend:
	cd $(BACKEND) && $(UV) run uvicorn db_query.main:app --reload --host $(HOST) --port $(PORT)

dev-frontend:
	cd $(FRONTEND) && npm run dev

lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND) && $(UV) run ruff check src tests

lint-frontend:
	cd $(FRONTEND) && npm run lint

test-backend:
	cd $(BACKEND) && $(UV) run pytest

build-frontend:
	cd $(FRONTEND) && npm run build

# 需先启动 dev-backend；需 curl（Git Bash / WSL / Linux）
openapi-json:
	curl -sS "http://127.0.0.1:$(PORT)/openapi.json"

clean-backend-cache:
	cd $(BACKEND) && rm -rf src/db_query/__pycache__ tests/__pycache__ .pytest_cache .ruff_cache 2>/dev/null || true

audit-frontend:
	cd $(FRONTEND) && npm audit

audit-fix-frontend:
	cd $(FRONTEND) && npm audit fix
