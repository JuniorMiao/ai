# HTTP API Contracts — `/api/v1`

**通用**

- **Base URL**：由部署决定，例如 `http://127.0.0.1:8000`。  
- **JSON**：请求/响应字段 **camelCase**（如 `createdAt`）。  
- **CORS**：允许任意 Origin（演示）。  
- **错误**：建议统一 `{ "error": { "code": string, "message": string } }`（camelCase）。

---

## GET `/api/v1/dbs`

列出已注册的数据库。

**200** body: `Array<{ name: string, createdAt?: string, updatedAt?: string }>`

---

## PUT `/api/v1/dbs/{name}`

创建或更新名为 `name` 的连接。

**Path**：`name` — 逻辑标识（URL 编码）。

**Body**

```json
{
  "url": "postgres://user:pass@host:5432/dbname"
}
```

**行为**：校验 URL 可达或可延迟首次连接；拉取 metadata 写入 SQLite。

**200/204**：成功；可返回 `{ "name": "...", "createdAt": "..." }`。

---

## GET `/api/v1/dbs/{name}`

返回缓存的 **metadata**（表/视图 JSON）。

**200**

```json
{
  "name": "mydb",
  "metadata": { },
  "fetchedAt": "2026-05-07T12:00:00Z"
}
```

**404**：未知 `name`。

---

## POST `/api/v1/dbs/{name}/query`

执行手写 SQL（须通过 sqlglot 单条 SELECT 校验与 LIMIT 策略）。

**Body**

```json
{
  "sql": "SELECT id, email FROM users LIMIT 10"
}
```

**200**

```json
{
  "columns": ["id", "email"],
  "rows": [[1, "a@b.com"]],
  "truncated": false,
  "maxRows": 1000
}
```

**400**：语法/策略不通过；**502**：目标 DB 错误。

---

## POST `/api/v1/dbs/{name}/query/natural`

根据自然语言生成 SQL；**不自动执行**或**生成后走与上面相同的执行管线**（推荐：先返回 `sql` 供前端展示，再由用户确认执行 —— 若 MVP 一键执行，须在任务中固定行为）。

**Body**

```json
{
  "prompt": "查询用户表的所有信息"
}
```

**200**（建议最小）

```json
{
  "sql": "SELECT * FROM users LIMIT 1000",
  "warnings": []
}
```

若设计为一键执行，则响应形状与 `query` 相同并增加 `generatedFromPrompt: true` 等字段。

---

## OpenAPI

实现阶段可用 FastAPI 自动生成 `/openapi.json`；本 README 为规格契约，可与生成文档对照评审。
