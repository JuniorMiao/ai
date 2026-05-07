# Implementation Plan: 数据库连接与自然语言查询（db-query-nl-demo）

**Branch**: `001-db-query-nl-demo` | **Date**: 2026-05-07 | **Spec**: [spec.md](./spec.md)  
**Input**: `instructions.md`（技术栈与 HTTP API，约第 23–56 行）+ `spec.md`

**Note**: 本文件由 `/speckit-plan` 生成；Phase 0/1 产出见同目录 `research.md`、`data-model.md`、`contracts/`、`quickstart.md`。

## Summary

在 `w2/db_query` 下交付 **FastAPI 后端**（uv、sqlglot、OpenAI 兼容 SDK）与 **React + Refine 5 + Tailwind + Ant Design** 前端（Monaco 作为 SQL 编辑器）。本地用 **SQLite** 持久化已登记的数据库连接 URL、缓存的模式元数据及 LLM 配置；对外 PostgreSQL 拉取 `information_schema`/目录信息并整理为 JSON 存入 SQLite。HTTP API 前缀 **`/api/v1`**，支持 **CORS 允许任意 Origin**（演示环境；生产需网络层收敛）。手写 SQL 与自然语言生成 SQL 均经 **sqlglot** 单条只读校验、默认 **LIMIT 1000**、AST/参数化策略防注入；响应 JSON **camelCase**。无登录（与宪章一致）。

## Technical Context

**Language/Version**: Python 3.12+（uv 管理）；TypeScript 5.x（前端，strict）；Node 20+（前端构建）  
**Primary Dependencies**: FastAPI、Uvicorn、Pydantic v2、sqlglot、httpx/openai（或兼容 OpenAI API 的 SDK）；React 18、Refine 5、Tailwind CSS、Ant Design、Monaco Editor（`@monaco-editor/react`）  
**Storage**: SQLite 文件 **`w2/db_query/db_query.db`**（相对 `specs/001-db-query-nl-demo/` 解析为 `../../db_query.db`，与 `instructions.md` 一致）；目标业务库为 PostgreSQL（规格假设）  
**Testing**: 后端 `pytest`；前端 Vitest/Playwright（按需，计划中后续任务细化）  
**Target Platform**: 本地开发者桌面浏览器 + 本机 FastAPI  
**Project Type**: Web 应用（前后端分离）  
**Performance Goals**: Demo 级；交互查询 p95 在 3 秒以内（不含用户网络与 LLM 延迟）；结果集上限 1000 行  
**Constraints**: 仅单条 `SELECT`；无认证；CORS `*`；密钥与连接串不进 Git（`.gitignore` + `.env.example`）；SQLite 路径可配置（默认上述路径）  
**Scale/Scope**: 单用户/小团队本地工具；非多租户生产服务  

### API 概要（与 `instructions.md` 对齐）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/dbs` | 列出已存储的逻辑库（不含明文密码时可返回掩码或省略） |
| PUT | `/api/v1/dbs/{name}` | 注册/更新连接，`body`: `{ "url": "<connection string>" }` |
| GET | `/api/v1/dbs/{name}` | 返回该库的缓存 metadata（表/视图 JSON） |
| POST | `/api/v1/dbs/{name}/query` | 执行校验后的 SQL，`body`: `{ "sql": "..." }` |
| POST | `/api/v1/dbs/{name}/query/natural` | NL→SQL，`body`: `{ "prompt": "..." }` |

## Constitution Check

*GATE: Phase 0 前通过；Phase 1 设计后再自检一遍。*  
*依据：`.specify/memory/constitution.md`*

| 项 | 结论 |
|----|------|
| 规格可追溯 | 本计划映射 `spec.md` FR-001–009；API 与栈映射 `instructions.md` 23–56。 |
| 范围最小 | 前后端 + 单 SQLite 文件 + 固定 API 面；无额外微服务。 |
| 安全红线 | 连接串/LLM Key 仅存本地 SQLite 或环境变量；仓库仅 `.env.example`；CORS `*` 视为演示债务，在 `research.md` 与 quickstart 中声明。 |
| 可验证性 | `spec.md` SC-001–004；本计划固化 **黄金问句 ≥5 条**（见下）与契约测试入口。 |
| 清晰可审 | 契约目录 `contracts/`；数据模型 `data-model.md`。 |
| db_query 子项目 | Ergonomic Python、TS strict、Pydantic、camelCase JSON、无必备认证 —— 已覆盖。 |

### 黄金自然语言问句（固化 SC-004，不少于 5 条）

在测试库（例如含 `users`、`orders` 类表）上选用：

1. 列出用户表中所有用户的邮箱和注册时间。  
2. 按金额从高到低显示最近 20 条订单。  
3. 统计每个状态下订单各自有多少条。  
4. 查询名称里包含「测试」的所有商品。  
5. 找出过去 7 天内创建的、金额大于 1000 的订单编号。

（实现阶段可将英文变体并列写入契约测试数据。）

## Project Structure

### Documentation (this feature)

```text
w2/db_query/specs/001-db-query-nl-demo/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── README.md          # 汇总 + OpenAPI 片段
└── tasks.md               # /speckit-tasks（本命令不生成）
```

### Source Code (`w2/db_query`)

```text
w2/db_query/
├── backend/
│   ├── pyproject.toml      # uv
│   ├── src/
│   │   └── db_query/       # FastAPI 应用、路由、服务、Pydantic 模型
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/                # Refine、页面、Monaco、API 客户端
├── db_query.db             # 运行时 SQLite（gitignore）
└── specs/001-db-query-nl-demo/
```

**Structure Decision**: 采用 **Option 2（Web 应用）** 变体，根目录落在 **`w2/db_query`**，与现有 Speckit 规格目录并列，避免与仓库根其它项目混淆。

## Complexity Tracking

本计划无宪章违规需豁免项；CORS 全开与无认证为 **产品明确演示约束**，已在 Constitution Check 与 `research.md` 记录风险与缓解（仅本地/可信网络使用）。

---

## Phase 0 — Research

**产出**：`research.md`（已完成）

已决议要点：**sqlglot** 作为解析与 AST 策略入口；**Pydantic `alias_generator`** 或字段 alias 实现 camelCase；**Refine** 使用 `dataProvider` 对接 REST；Monaco 只做编辑器不负责校验（校验在后端）。

## Phase 1 — Design & Contracts

**产出**：

- `data-model.md`：SQLite 表与实体关系。  
- `contracts/README.md`：REST 路径、请求/响应 camelCase 字段说明及错误形状。  
- `quickstart.md`：uv/npm 命令、环境变量、启动顺序。

**Agent 上下文**：已更新 `.cursor/rules/specify-rules.mdc`，指向本 `plan.md`。

## Constitution Check（Phase 1 后复审）

- Pydantic 模型与 OpenAPI 导出字段名为 **camelCase**。  
- 路由层 **CORSMiddleware** `allow_origins=["*"]` 与说明文档一致。  
- SQL 执行层统一走 **sqlglot 校验 + 限流行数**，NL 分支生成的文本在进入执行前与手写路径同一套校验。
