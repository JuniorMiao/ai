# Data Model: db-query-nl-demo

**存储**：SQLite（`w2/db_query/db_query.db`，可配置）  
**外部 DB**：PostgreSQL 连接串由用户通过 API 提供。

## 本地 SQLite 逻辑表（建议）

### `registered_database`

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | TEXT PK | 逻辑名，对应路径 `{name}` |
| `url_encrypted` 或 `url` | TEXT | 连接串；若 MVP 明文存储须在文档中警示，后续改为加密或仅引用 env |
| `created_at` | TEXT ISO8601 | 创建时间 |
| `updated_at` | TEXT ISO8601 | 更新时间 |

### `database_metadata`

| 字段 | 类型 | 说明 |
|------|------|------|
| `db_name` | TEXT PK FK | 关联 `registered_database.name` |
| `payload_json` | TEXT | 表/视图结构 JSON（由 PG 目录 + 可选 LLM 整理） |
| `fetched_at` | TEXT ISO8601 | 上次成功拉取时间 |
| `schema_version` | INTEGER | 可选，用于失效判断 |

### `llm_settings`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增 |
| `provider` | TEXT | 如 `openai` / `azure` |
| `base_url` | TEXT | API Base URL |
| `api_key_ref` | TEXT | 环境变量名或加密占位；不存 Git |
| `model` | TEXT | 模型 id |
| `is_default` | INTEGER 0/1 | 默认配置 |

## API / Pydantic 映射（camelCase）

- `RegisteredDatabase` → `name`, `createdAt`, `updatedAt`（列表接口可省略 URL）  
- `DatabaseMetadataResponse` → `name`, `metadata`, `fetchedAt`  
- `QueryRequest` → `sql`  
- `NaturalQueryRequest` → `prompt`  
- `QueryResult` → `columns`, `rows`, `truncated`, `maxRows`, `error`（可选）

## 关系

- `registered_database` 1 — 1 `database_metadata`（按 `name`）  
- `llm_settings` 多行可选；NL 端点使用 `is_default` 或请求内指定 id（若后续扩展）。
