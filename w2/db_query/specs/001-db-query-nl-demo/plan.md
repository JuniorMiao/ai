# Implementation Plan: db-query-nl-demo

**Branch**: `001-db-query-nl-demo` | **Date**: 2026-04-28 | **Spec**: `specs/001-db-query-nl-demo/spec.md`  
**Input**: Feature specification from `/specs/001-db-query-nl-demo/spec.md`

## Summary

构建一个**只读、小 schema、可校验**的自然语言查询 Demo：优先落地规则/模板路径，可选接入 LLM 生成受约束 `SELECT`；通过 Cursor + Spec Kit 维护规格与任务，满足仓库宪章。

## Technical Context

**Language/Version**: Python 3.11+（建议；若团队偏好 Node 可在实现前修订本文件）  
**Primary Dependencies**: `sqlite3`（标准库）；可选 `pydantic` 做配置校验；可选官方 OpenAI 兼容客户端用于 Text-to-SQL（仅当启用时）  
**Storage**: SQLite 文件（`data/seed.sqlite` 或 `w2/db_query/data/seed.sqlite`，路径在任务中固化）  
**Testing**: `pytest` 与黄金问句 JSON/YAML  
**Target Platform**: Windows / macOS / Linux 本地 CLI  
**Project Type**: CLI 或小入口模块 + `tests/`  
**Performance Goals**: 单次查询 p95 < 2s（不含外部 LLM 时 < 500ms）  
**Constraints**: 仅 `SELECT`；单连接只读；结果默认上限 500 行  
**Scale/Scope**：单库 ≤5 表；Demo 级数据量  

## Constitution Check

- **规格可追溯**：本计划与任务映射 `spec.md` 中 FR/SC 与用户故事。  
- **范围最小**：不引入通用 BI、不连生产库。  
- **安全红线**：`.env.example` 无秘密；禁止将 `.env` 提交。  
- **可验证性**：黄金问句 + pytest；README 一键命令。  
- **清晰可审**：NL→校验→执行 分层目录与命名在任务中体现。

## Project Structure

### Documentation (this feature)

```text
specs/001-db-query-nl-demo/
├── spec.md
├── plan.md
├── tasks.md
```

### Source (proposed)

```text
w2/db_query/                    # 或仓库根下 src/db_query_demo/，以 tasks 为准
├── README.md
├── .env.example
├── data/
│   └── seed.sqlite            # 构建或提交小 seed（二选一在任务中说明）
├── src/                       # 包名待定
└── tests/
    └── test_golden_queries.py
```

## Complexity Tracking

> 无额外复杂度登记；若引入 LLM 路径，须在合并前补充威胁建模一行于 `research.md`（可选）。

## Phases

### Phase 0 — Outline（本文件已覆盖高层）

### Phase 1 — Design

- 固化 schema 与黄金问句文件格式。
- SQL 校验规则列表（关键字、多语句、白名单）。

### Phase 2 — Implementation

- Seed + 校验层 + 规则引擎 MVP。
- 可选 LLM 适配器（接口与实现分离）。

### Phase 3 — Verification

- pytest 与 README 复现步骤。

## Phase 0 Research

（可选）若选定 LLM 提供商，记录速率限制与「失败时降级」行为；否则标 N/A。

## Phase 1 Design

详见 `tasks.md` 中设计与实现任务；`data-model.md` 可在首版用 `spec.md` Key Entities 代替，后续再拆文件。
