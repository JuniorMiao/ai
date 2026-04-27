# 自然语言查询数据 Demo — 入手分析

**文档性质**：对「用 Cursor 辅助编程实现 NL→数据查询 Demo」的**入手路线**与**宪章对齐**分析。正式 Speckit 工件见 `specs/001-db-query-nl-demo/`。  
**生成日期**：2026-04-28  
**更新**：已建立 feature 分支 `001-db-query-nl-demo` 与 `spec.md` / `plan.md` / `tasks.md`；在**该分支**上可运行 `check-prerequisites.ps1` 与 `/speckit-analyze`。

---

## 1. 当前状态与 Speckit 前置

| 项 | 状态 |
|----|------|
| Feature 分支 | `001-db-query-nl-demo`（与 slug `db-query-nl-demo` 对应） |
| Speckit 三件套 | `specs/001-db-query-nl-demo/spec.md`、`plan.md`、`tasks.md` |
| 本分析输出 | `w2/db_query/spec/analysis.md`（与正式 spec 交叉引用） |

**下一步**：`git checkout 001-db-query-nl-demo` 后运行 `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`，再执行 `/speckit-analyze`。

---

## 2. 与项目宪章（`.specify/memory/constitution.md`）的对齐

| 原则 | 对 Demo 的含义 |
|------|----------------|
| **I. 规格优先** | 在写实现代码前，用一页纸写清：用户能问什么、数据从哪来、哪些查询合法；随后用 Speckit 固化到 `spec/plan/tasks`。 |
| **II. 最小范围** | Demo 只做「只读 + 单库/单文件数据源 + 明确 schema」，不扩散到通用 BI、多租户、复杂权限。 |
| **III. 安全与密钥** | 数据库连接串、API Key **仅环境变量**；仓库内保留 `.env.example`；若用云端模型，**不落库**用户自然语言原文或打码说明。 |
| **IV. 可验证** | 验收清单：给定 5～10 条中文/英文问句，期望得到正确行集或等价 SQL；可用脚本或快照测试固化。 |
| **V. 清晰可审查** | NL→查询 的管道（解析 → 校验 → 执行）分模块；对「为何允许执行这条 SQL」保留日志或说明字段。 |

---

## 3. Demo 目标边界（建议先写进未来 `spec.md`）

- **用户**：开发者或内部试用者；非面向公网匿名用户（降低滥用与注入面）。  
- **数据**：极小、**只读**、schema **固定**（例如 `orders(id, customer, amount, date)` 或一份版本化的 `seed.sqlite`）。  
- **「自然语言」**：指中文/英文短句 → **受约束的查询**（见下文路线），不承诺开放域任意问题。  
- **Cursor 角色**：规格与任务拆解、生成样板代码、通过 **Skill / Rules / MCP** 约束 Agent 行为，而不是「完全放手让模型连生产库」。

---

## 4. 技术路线对比（怎么选）

### 4.1 按复杂度递增（推荐顺序）

1. **规则 + 关键词/槽位（最稳）**  
   - 预定义意图：`销售额`、`按客户分组` → 映射到固定 SQL 模板。  
   - **优点**：无模型也可跑通；最易验收。  
   - **缺点**：「自然」程度有限；适合 Demo 第一期证明链路。

2. **小模型/大模型 Text-to-SQL（在沙箱内）**  
   - 把 **完整 schema（含类型、示例行）** 注入 prompt；输出 **仅** `SELECT`；再经 **静态校验**（禁止 `INSERT/UPDATE/DELETE`、多语句、`;` 后拼接等）。  
   - 执行前用 **只读连接** + **超时** + **行数上限**。  
   - **优点**：NL 体验好。  
   - **风险**：幻觉 SQL；必须用校验层兜底（宪章 IV）。

3. **向量检索 + 结构化过滤（RAG 式）**  
   - 文档/行描述向量化，先检索相关表或行，再生成 SQL 或直接在结果集上过滤。  
   - **优点**：表多、说明多时更稳。  
   - **缺点**：实现与调参成本高于 Demo 需求时可延后。

### 4.2 与 Cursor 的结合点

| 能力 | 用途 |
|------|------|
| **Spec Kit** | 把「允许的问题类型、数据源、安全约束」写进 spec/plan/tasks，实现与宪章 I 一致。 |
| **`.cursor/rules` / Skills** | 固化「生成 SQL 时必须带校验步骤」「禁止写密钥」等团队约束。 |
| **MCP（可选）** | 只读数据库 MCP：由工具执行查询，模型不直接握连接串；适合后续扩展。 |
| **CLI `agent` / IDE** | 在仓库内迭代实现与测试命令，保持可重复验证（宪章 IV）。 |

---

## 5. 推荐入手顺序（可执行 checklist）

1. **建 feature 分支**（符合 Speckit 命名，如 `001-db-query-nl-demo`）。  
2. **在 `w2/db_query/`（或 Speckit 分配的 FEATURE_DIR）写最小 `spec.md`**：用户故事 1～2 条、非功能约束（只读、超时、行数上限）、示例问句与期望。  
3. **选栈**：例如 Python + SQLite + `sqlite3` 只读；或 Node + `better-sqlite3`（只读打开）。  
4. **实现顺序**：  
   - 固定 schema + seed 数据；  
   - 手写 2～3 条 SQL 模板跑通 E2E；  
   - 加 **SQL 校验层**；  
   - 再接 LLM 生成 SQL（可选）；  
   - 最后补 README 与 `.env.example`。  
5. **跑 `/speckit-plan` / `/speckit-tasks`**，将任务拆到可提交粒度；实现后再 `/speckit-analyze`。  
6. **验收**：脚本或表格记录「问句 → 是否通过校验 → 结果行数/关键字段」，满足宪章 **可验证**。

---

## 6. 风险与缓解

| 风险 | 缓解 |
|------|------|
| SQL 注入 / 多语句 | 仅允许单条 `SELECT`；白名单表名/列名；参数化或严格 AST 检查。 |
| 密钥进库 | `.gitignore` 覆盖 `.env`；PR 自检 secret 扫描。 |
| 范围膨胀 | 写死「不支持 JOIN 超过两表」等，在 spec 中明示。 |
| 模型幻觉 | 校验失败时返回错误信息给用户，不执行；记录 prompt 版本便于复现。 |

---

## 7. 结论与下一步

- **入手点**：先满足 **宪章 I + III + IV**——feature 分支 + 一页 spec + 只读小数据集 + 校验层 + 可重复验收；NL 能力从 **规则模板** 或 **受约束 Text-to-SQL** 二选一启动，避免一步到位「任意问答」。  
- **与 Cursor 的关系**：用 Speckit 与 Cursor Rules/Skills 把「能做什么、不能做什么」钉在仓库里，代码生成始终有锚点。  
- **立即动作**：创建 `001-*` 分支 → 在 feature 目录生成 `spec.md`（可将本节 3、5、6 压缩为需求条目）→ 执行 `check-prerequisites` 通过后调用 `/speckit-plan`。

---

## 8. 参考（仓库内）

- 宪章：`.specify/memory/constitution.md`  
- 前置脚本：`.specify/scripts/powershell/check-prerequisites.ps1`  
- 分析技能：`.cursor/skills/speckit-analyze/SKILL.md`  

如需将本文吸收进正式 Speckit 流程，建议在合并前进 feature 分支并复制/迁移本节要点至 `spec.md` 的「概述 / 功能需求」中，避免双源维护。
