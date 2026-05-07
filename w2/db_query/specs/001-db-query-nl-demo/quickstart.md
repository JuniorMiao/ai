# Quickstart: db-query-nl-demo

## 前置

- Python 3.12+，已安装 **uv**  
- Node.js 20+，**pnpm** 或 **npm**  
- 可选：本地 **PostgreSQL**（用于验收连接）

## 后端（`w2/db_query/backend`）

```bash
cd w2/db_query/backend
uv sync
# 可选：复制环境变量
cp .env.example .env
```

**环境变量（示例）**

| 变量 | 说明 |
|------|------|
| `DB_QUERY_SQLITE_PATH` | SQLite 文件路径；默认 `../db_query.db`（相对 backend cwd）或 Plan 中绝对默认 |
| `OPENAI_API_KEY` | NL 功能如需默认模型 |

启动：

```bash
uv run uvicorn db_query.main:app --reload --host 0.0.0.0 --port 8000
```

验证：浏览器打开 `http://127.0.0.1:8000/docs`。

## 前端（`w2/db_query/frontend`）

```bash
cd w2/db_query/frontend
npm install
npm run dev
```

将 `.env` 中 **`VITE_API_URL`**（或 Refine 使用的变量）指向 `http://127.0.0.1:8000`。

## 登记数据库并查询（curl）

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/dbs/demo ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"postgres://postgres:postgres@localhost:5432/postgres\"}"

curl http://127.0.0.1:8000/api/v1/dbs/demo

curl -X POST http://127.0.0.1:8000/api/v1/dbs/demo/query ^
  -H "Content-Type: application/json" ^
  -d "{\"sql\":\"SELECT 1 AS x\"}"
```

## 安全提示

- **CORS `*`** 与 **无认证** 仅适合本地/可信网段。  
- 不要把含密码的 `db_query.db` 或 `.env` 提交到 Git。
