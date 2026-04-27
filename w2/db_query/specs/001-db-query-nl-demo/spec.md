# Feature Specification: 自然语言查询数据 Demo（db-query-nl-demo）

**Feature Branch**: `001-db-query-nl-demo`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: 利用 Cursor 辅助编程，实现受约束的自然语言 → 只读数据查询的演示项目（slug: `db-query-nl-demo`）。

**相关分析**：`w2/db_query/spec/analysis.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 用自然语言得到查询结果（Priority: P1）

作为演示使用者，我希望用中文或英文短句描述查询意图（例如「列出金额大于 100 的订单」），系统在**校验通过后**返回只读查询的结果（表格或 JSON），以便验证 NL→数据 的闭环。

**Why this priority**：核心价值；无此条则 Demo 不成立。

**Independent Test**：使用固定 seed 数据库与 5～10 条黄金问句，脚本或手工比对结果集与期望。

**Acceptance Scenarios**:

1. **Given** 已加载只读 SQLite seed，**When** 提交一条在允许范围内的问句，**Then** 返回与等价 SQL 一致的非空或空结果集，且响应时间小于约定上限（如 5s）。
2. **Given** 同一数据库，**When** 提交含危险关键字或多语句的问句，**Then** 拒绝执行并返回可读错误，不访问未授权表。

---

### User Story 2 - 配置与文档可复现（Priority: P2）

作为开发者，我希望通过 `.env.example` 与 README 完成环境配置，且不将密钥写入仓库，以便他人可重复运行与验证。

**Why this priority**：宪章要求可验证与密钥红线。

**Independent Test**：全新 clone 后仅按 README 步骤可跑通查询（可选用占位 API Key 跳过真实 LLM，仅用规则模板路径）。

**Acceptance Scenarios**:

1. **Given** 未配置真实密钥，**When** 按 README 使用示例环境变量，**Then** 至少一种模式（规则模板）可完成 US1 中一条黄金用例。

---

### Edge Cases

- 问句无法映射到任何允许意图时，应提示「无法理解」并给出示例问法。
- LLM 不可用或超时时，应降级到规则模板或明确失败（不静默返回错误数据）。
- 结果行数超过上限时截断并标注「仅显示前 N 行」。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**：系统 MUST 仅对**预先声明**的数据源执行**只读**查询（建议 SQLite seed，单文件版本化）。
- **FR-002**：系统在执行前 MUST 对生成的或映射得到的 SQL 做**静态校验**（例如仅允许 `SELECT`、禁止多语句、表名白名单）。
- **FR-003**：系统 MUST 支持至少一种 NL 路径：**规则/模板映射**；MAY 在此基础上增加受约束的 **Text-to-SQL**（可选 LLM）。
- **FR-004**：密钥与连接串 MUST 来自环境变量；仓库 MUST 提供不含秘密的 `.env.example`。
- **FR-005**：系统 MUST 提供可重复的验收方式（脚本、Makefile 目标或文档中的固定命令与期望摘要）。

### Success Criteria *(mandatory)*

- **SC-001**：黄金问句集（≥5 条）在 CI 或本地一键命令下全部通过或明确标记为「需 API Key 跳过」。
- **SC-002**：对注入样例（多语句、非白名单表）100% 拦截且不执行。

### Key Entities *(include if feature involves data)*

- **QueryRequest**：自然语言文本、可选会话 id（不落库敏感原文时可省略持久化）。
- **QueryResult**：列名、行数据、截断标记、所用模式（规则 / LLM）。

## Assumptions

- Demo 不面向公网匿名用户；不实现完整多租户权限模型。
- 实现语言栈可在 `plan.md` 中最终确定（Python 或 Node 均可）。
