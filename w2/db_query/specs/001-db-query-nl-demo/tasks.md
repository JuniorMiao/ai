---
description: "Task list for db-query-nl-demo (001)"
---

# Tasks: 数据库连接与自然语言查询（db-query-nl-demo）

**Input**: Design documents from `w2/db_query/specs/001-db-query-nl-demo/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md), [contracts/README.md](./contracts/README.md), [research.md](./research.md), [quickstart.md](./quickstart.md)

**Tests**: 规格未强制 TDD；本清单不含独立测试任务。SC-002 拦截用例在 Polish 阶段以可选 pytest 覆盖。

**Organization**: 按 `spec.md` 用户故事优先级（P1→P3）分阶段；路径遵循 `plan.md` 的 `w2/db_query/backend` 与 `w2/db_query/frontend`。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、互不依赖）
- **[USn]**: 用户故事标签（仅用户故事阶段）

## Path Conventions

- 后端：`w2/db_query/backend/src/db_query/`
- 前端：`w2/db_query/frontend/src/`
- 测试：`w2/db_query/backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 初始化 monorepo 子项目与工具链

- [x] T001 Create directory layout `w2/db_query/backend/`, `w2/db_query/frontend/`, `w2/db_query/backend/src/db_query/`, `w2/db_query/backend/tests/` per `plan.md`
- [x] T002 Initialize Python package with uv in `w2/db_query/backend/pyproject.toml` (FastAPI, Uvicorn, Pydantic v2, pydantic-settings, sqlglot, asyncpg or psycopg, openai, httpx, ruff, pytest)
- [x] T003 [P] Initialize Vite + React + TypeScript strict in `w2/db_query/frontend/` with Refine 5, Ant Design, Tailwind CSS, `@monaco-editor/react`
- [x] T004 [P] Add `w2/db_query/backend/.env.example` documenting `DB_QUERY_SQLITE_PATH` and `VITE_API_URL` / `OPENAI_API_KEY` placeholders
- [x] T005 [P] Add `w2/db_query/frontend/.env.example` with `VITE_API_BASE_URL=http://127.0.0.1:8000`
- [x] T006 [P] Configure Ruff and pytest in `w2/db_query/backend/pyproject.toml`
- [x] T007 [P] Configure ESLint and `tsconfig.json` strict mode in `w2/db_query/frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SQLite、应用壳、CORS、配置 —— 完成前不得开始用户故事功能开发

**Checkpoint**: Foundation ready

- [x] T008 Implement SQLite schema DDL for `registered_database`, `database_metadata`, `llm_settings` in `w2/db_query/backend/src/db_query/storage/schema.sql`
- [x] T009 Implement connection and migration-on-boot helper in `w2/db_query/backend/src/db_query/storage/sqlite.py` using `DB_QUERY_SQLITE_PATH`
- [x] T010 Create Pydantic settings module in `w2/db_query/backend/src/db_query/config.py` (sqlite path, default max rows 1000)
- [x] T011 Create FastAPI app factory with `CORSMiddleware(allow_origins=["*"])` in `w2/db_query/backend/src/db_query/main.py`
- [x] T012 Add lifespan hook to initialize SQLite and attach to `app.state` in `w2/db_query/backend/src/db_query/main.py`
- [x] T013 [P] Add unified error JSON model `{ error: { code, message } }` (camelCase aliases) in `w2/db_query/backend/src/db_query/schemas/errors.py`
- [x] T014 [P] Add exception handlers registration in `w2/db_query/backend/src/db_query/main.py`

---

## Phase 3: User Story 1 — 添加连接并浏览表与视图 (Priority: P1) 🎯 MVP

**Goal**: `GET/PUT /api/v1/dbs`、`GET /api/v1/dbs/{name}`；前端列表 + 元数据展示  
**Independent Test**: 见 `spec.md` US1：有效连接返回表/视图或空库说明；无效连接返回错误

- [x] T015 [P] [US1] Add database DTOs (`RegisteredDatabaseListItem`, `PutDatabaseBody`, `DatabaseMetadataResponse`) with camelCase in `w2/db_query/backend/src/db_query/schemas/databases.py`
- [x] T016 [US1] Implement `registered_database` / `database_metadata` persistence in `w2/db_query/backend/src/db_query/repositories/databases.py`
- [x] T017 [US1] Implement PostgreSQL introspection (tables/views/columns) in `w2/db_query/backend/src/db_query/services/metadata.py` and serialize to JSON for `payload_json`
- [x] T018 [US1] Implement `GET /api/v1/dbs`, `PUT /api/v1/dbs/{name}`, `GET /api/v1/dbs/{name}` in `w2/db_query/backend/src/db_query/api/dbs.py` per `contracts/README.md`
- [x] T019 [US1] Include router from `w2/db_query/backend/src/db_query/api/dbs.py` in `w2/db_query/backend/src/db_query/main.py`
- [x] T020 [P] [US1] Add typed API client for `/api/v1/dbs` in `w2/db_query/frontend/src/api/databases.ts`
- [x] T021 [US1] Configure Refine `dataProvider` or equivalent REST hooks in `w2/db_query/frontend/src/App.tsx`
- [x] T022 [US1] Build database list and add-or-update connection form in `w2/db_query/frontend/src/pages/databases/ListPage.tsx`
- [x] T023 [US1] Build metadata tree/table view in `w2/db_query/frontend/src/pages/databases/DetailPage.tsx`

**Checkpoint**: US1 可独立演示

---

## Phase 4: User Story 2 — 只读 SQL 查询与表格结果 (Priority: P2)

**Goal**: sqlglot 单条 SELECT 校验、默认 LIMIT 1000、`POST /api/v1/dbs/{name}/query`；Monaco + 表格  
**Independent Test**: 见 `spec.md` US2：合法 SELECT 返回行列；非法语句 400；无 LIMIT 时行数 ≤1000 且 `truncated`/`maxRows` 可见

- [x] T024 [US2] Implement `validate_and_apply_limit` using sqlglot (single SELECT, reject DML/multi-statement) in `w2/db_query/backend/src/db_query/services/sql_guard.py`
- [x] T025 [US2] Implement read-only execution returning columns/rows in `w2/db_query/backend/src/db_query/services/query_runner.py`
- [x] T026 [P] [US2] Add `QueryRequest` / `QueryResult` Pydantic models (camelCase) in `w2/db_query/backend/src/db_query/schemas/query.py`
- [x] T027 [US2] Implement `POST /api/v1/dbs/{name}/query` in `w2/db_query/backend/src/db_query/api/query.py`
- [x] T028 [US2] Register query router in `w2/db_query/backend/src/db_query/main.py`
- [x] T029 [P] [US2] Add `POST` query helper in `w2/db_query/frontend/src/api/query.ts`
- [x] T030 [P] [US2] Create Monaco wrapper component in `w2/db_query/frontend/src/components/SqlEditor.tsx`
- [x] T031 [US2] Build SQL workspace with Run and Ant Design `Table` for results in `w2/db_query/frontend/src/pages/query/SqlQueryPage.tsx`

**Checkpoint**: US1 + US2 均可独立验收

---

## Phase 5: User Story 3 — 自然语言生成 SQL 与 LLM 配置复用 (Priority: P3)

**Goal**: `llm_settings` 持久化、OpenAI 兼容调用、`POST /api/v1/dbs/{name}/query/natural`；前端 NL 入口与设置页  
**Independent Test**: 见 `spec.md` US3 与 `plan.md` 黄金问句；生成 SQL 须经 `sql_guard`；无配置时引导设置

- [x] T032 [P] [US3] Add LLM settings DTOs in `w2/db_query/backend/src/db_query/schemas/llm.py`
- [x] T033 [US3] Implement `llm_settings` repository in `w2/db_query/backend/src/db_query/repositories/llm_settings.py`
- [x] T034 [US3] Expose minimal `GET/PUT` (or `PATCH`) LLM config endpoints in `w2/db_query/backend/src/db_query/api/llm_settings.py`
- [x] T035 [US3] Implement NL→SQL with metadata context and strict system prompt in `w2/db_query/backend/src/db_query/services/nl_sql.py`
- [x] T036 [US3] Implement `POST /api/v1/dbs/{name}/query/natural` returning `{ sql, warnings }` then optionally reuse `query_runner` if product chooses execute-on-generate in `w2/db_query/backend/src/db_query/api/natural_query.py`
- [x] T037 [US3] Register LLM and natural routers in `w2/db_query/backend/src/db_query/main.py`
- [x] T038 [P] [US3] Add frontend API for natural query and LLM settings in `w2/db_query/frontend/src/api/natural.ts`
- [x] T039 [P] [US3] Build LLM configuration form in `w2/db_query/frontend/src/pages/settings/LlmSettingsPage.tsx`
- [x] T040 [US3] Extend query UI with NL prompt, generate flow, and empty-config guard in `w2/db_query/frontend/src/pages/query/NaturalQueryPanel.tsx`

**Checkpoint**: 三则用户故事均可演示

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 文档、SC-002 样例、与 quickstart 一致

- [ ] T041 [P] Add pytest cases for injection/abuse SQL samples (expect reject before DB) in `w2/db_query/backend/tests/test_sql_guard.py` targeting `sql_guard.py`
- [ ] T042 Update `w2/db_query/specs/001-db-query-nl-demo/quickstart.md` with final module paths, ports, and curl examples matching implementation
- [ ] T043 Add `w2/db_query/README.md` linking to `w2/db_query/specs/001-db-query-nl-demo/plan.md` and run instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → **Phase 2** → **Phase 3–5**（US 可按优先级顺序或 US2/US3 在 US1 合并后接续）→ **Phase 6**
- **Phase 2 未完成前**：不得实现业务路由与前端页面（T015 起）

### User Story Dependencies

- **US1**：仅依赖 Phase 2
- **US2**：逻辑上需已注册的 DB（US1 的 API）；可单独用 curl/契约验收 runner
- **US3**：需 US1 的 metadata 与 US2 的 `sql_guard`/`query_runner` 复用

### Parallel Opportunities

- **Phase 1**: T003、T004、T005、T006、T007 可与 T002 并行（不同侧）
- **Phase 2**: T013、T014 可与 T010 并行（不同文件）
- **US1**: T015、T020 并行；T022/T023 在 API 就绪后并行度低需联调
- **US2**: T026、T029、T030 可在后端 T024–T027 分支上并行准备前端
- **US3**: T032、T038、T039 可先行建模与 UI 骨架

### Parallel Example: User Story 2

```text
# 后端守卫与执行 vs 前端编辑器壳
T024 w2/db_query/backend/src/db_query/services/sql_guard.py
T030 w2/db_query/frontend/src/components/SqlEditor.tsx
```

---

## Implementation Strategy

### MVP First（仅 US1）

1. Phase 1 + Phase 2  
2. Phase 3（T015–T023）  
3. 按 `spec.md` SC-001 手工验收后暂停

### Incremental Delivery

1. US1 → 演示连接与元数据  
2. US2 → 演示安全只读查询与表格  
3. US3 → 演示 NL 与 LLM 配置  

### Suggested MVP Scope

- **MVP = Phase 1 + Phase 2 + Phase 3（US1）**；任务数 **23**（T001–T023）

---

## Notes

- 所有对外 JSON 字段 **camelCase**（宪章 + `contracts/README.md`）
- 连接串与 API key 不得入 Git；仅 `.env.example` 与本地 SQLite（已在仓库 `.gitignore`）
- NL 端点行为（仅返回 SQL vs 一键执行）在 T036 中选一并写入 `natural_query.py` 注释
