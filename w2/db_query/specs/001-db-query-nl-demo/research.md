# Research: db-query-nl-demo

**日期**：2026-05-07  
**输入**：`plan.md` Technical Context、`instructions.md` 23–56、`spec.md`

## 1. SQL 校验与注入防护

**Decision**：使用 **sqlglot** 解析用户 SQL 与 NL 产出 SQL，约束为**单表达式**、**SELECT**、禁止危险构造；必要时结合方言 `postgres`；拒绝后再访问目标库。

**Rationale**：与 `instructions.md` 一致；纯 AST 可比正则更稳；与「参数化 / AST 检查」规格对齐。

**Alternatives considered**：仅 `sqlparse`（类型推断较弱）；自建正则（易漏）。

## 2. 默认 LIMIT 1000

**Decision**：若解析后的 AST 无 `LIMIT`，在通过校验后注入 `LIMIT 1000`（或对 Driver 使用等价参数），并在响应中带 `truncated` / `maxRows` 等 camelCase 字段提示。

**Rationale**：对齐 `spec.md` FR-004 / SC-003。

## 3. JSON camelCase（API）

**Decision**：Pydantic v2 模型使用 **`model_config = ConfigDict(alias_generator=to_camel)`** 或显式 `Field(alias="...")`；FastAPI `response_model_by_alias=True`。

**Rationale**：宪章 db_query 段强制对外 camelCase。

## 4. CORS 允许所有 Origin

**Decision**：`CORSMiddleware(..., allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])`（或与 FastAPI 文档推荐等价配置）。

**Rationale**：`instructions.md` 明确要求；适用于本地 Demo。

**Risk**：任意站点若可访问用户浏览器中的 API Origin 则存在 CSRF/滥用面；**缓解**：文档声明仅可信网络/localhost；生产应改白名单。

## 5. SQLite 路径

**Decision**：默认数据库文件 **`w2/db_query/db_query.db`**（由 `specs/001-db-query-nl-demo/../../db_query.db` 解析）。通过环境变量 **`DB_QUERY_SQLITE_PATH`** 可覆盖。

**Rationale**：与说明文档路径一致；便于 `.gitignore` 单文件。

## 6. OpenAI SDK 与自然语言

**Decision**：使用官方 **`openai`** Python 包（或兼容 **LiteLLM**/自建 HTTP），由用户配置的 **baseUrl + apiKey** 调用；Prompt 注入当前库的 metadata JSON（来自 SQLite 缓存）。

**Rationale**：`instructions.md` 指定 openai sdk；多供应商可通过兼容 Base URL 扩展。

## 7. 前端栈

**Decision**：**Refine 5** + **Ant Design** + **Tailwind**；数据获取使用自定义 **`dataProvider`** 调用上述 REST；SQL 编辑使用 **Monaco**。

**Rationale**：与说明一致；Refine 适合 CRUD 型「连接列表 + 查询页」。

## 8. 密钥存储 vs 宪章 III

**Decision**：LLM API Key **默认建议环境变量** `OPENAI_API_KEY` 或首启用户在 UI 录入后写入 **SQLite 用户目录外** 或 OS keychain 为后续增强；MVP 可写入 SQLite **加密字段或提示用户风险** —— 实现任务阶段在 `tasks.md` 拆「最小可用」与「加固」。

**Rationale**：宪章禁止密钥入库（Git）；本地 SQLite 非 Git，但仍属敏感落盘，须在 `quickstart.md` 写明。
