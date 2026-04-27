# Tasks: db-query-nl-demo

**Input**: `specs/001-db-query-nl-demo/spec.md`, `plan.md`  
**Prerequisites**: plan.md, spec.md

**Tests**: 包含黄金问句自动化测试（宪章可验证性）。

## Phase 1: Setup

- [ ] T001 [P] 在 `w2/db_query/` 创建 `README.md`、`.env.example`（无秘密）、`data/`、`src/`、`tests/` 目录骨架
- [ ] T002 在 `w2/db_query/README.md` 写明：依赖安装、设置环境变量、运行测试与一次示例 NL 查询命令

## Phase 2: Foundational

- [ ] T003 添加 `w2/db_query/data/schema.sql` 与构建脚本或说明，生成只读 `seed.sqlite`（表结构符合 spec 中 Key Entities 演示需要，如 `orders`）
- [ ] T004 实现 `w2/db_query/src/sql_guard.py`（或等价模块）：仅允许 `SELECT`、单语句、表名白名单、可选行数 LIMIT 注入
- [ ] T005 [P] 添加 `w2/db_query/tests/fixtures/golden_queries.yaml`（≥5 条问句 + 期望行数或关键列断言）

## Phase 3: User Story 1 - 自然语言查询（P1）

- [ ] T006 [US1] 实现 `w2/db_query/src/rule_engine.py`：将预定义意图/关键词映射到参数化 SQL，所有 SQL 经 T004 校验后执行
- [ ] T007 [US1] 实现 `w2/db_query/src/cli.py`（或 `__main__.py`）：读取问句、调用 rule_engine、打印表格/JSON
- [ ] T008 [US1] 实现 `w2/db_query/tests/test_golden_queries.py`：对 golden 文件跑集成测试，覆盖 FR-002 / SC-002 拦截用例
- [ ] T009 [US1] （可选）[P] 若启用 LLM：增加 `w2/db_query/src/llm_sql.py`，生成 SQL 后**必须**经 T004；`.env.example` 增加 `OPENAI_API_KEY` 或等价占位说明

## Phase 4: User Story 2 - 文档与复现（P2）

- [ ] T010 [US2] 校验 `README.md` 与 `.env.example` 满足 FR-004；在 CI 或 `pytest` 中增加「无密钥时跳过 LLM 用例」标记
- [ ] T011 [US2] 在 `w2/db_query/spec/analysis.md` 或本 feature 目录添加「与 spec 差异」简短说明（若分析文档与实现路径不一致时更新）

## Dependencies

- T003–T005 阻塞 T006–T008  
- T004 阻塞任何执行 SQL 的路径  
- T008 完成后可并行 T009（可选）与 T010

## Parallel Example

- T001 可与审阅 `spec.md` 并行（人工）  
- T005 可与 T004 并行（不同文件）
