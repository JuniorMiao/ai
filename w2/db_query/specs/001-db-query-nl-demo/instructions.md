# Instructions

## constitution
这是针对 F:\AI-learn\ai\w2\db_query 项目的:
- 后端使用 Ergonomic Python 风格来编写代码，前端使用 typescript
- 前后端都要有严格的类型标注
- 使用 pydantic 来定义数据模型
- 所有后端生成的 JSON 数据，使用 camelCase 格式。
- 不需要 authentication，任何用户都可以使用。

## 基本思路
这是一个数据库查询工具，用户可以添加db url，系统会自动连接到数据库，获取数据库的metadata信息，将table和view信息展示出来。用户可以自己输入sql查询，也可以输入自然语言生成sql查询。

基本想法
- 数据库连接字符串和数据库的metadata都会存储到sqlite数据库中。用户可以根据postgresql的功能查询系统中的表和视图信息，用LLM将这些信息转换成json格式，存储到sqlite数据库中。以后可以复用这些信息。
- 当用户使用LLM通过自然语言生成sql查询时，系统可以读取表和视图的信息作为context传给LLM，LLM会根据这些信息生成查询sql。
- 当用户通过自然语言生成sql查询时，需要提示用户选择LLM的api和对应的api-key，如果没有可选项，需要用户手动输入，并将信息存储到sqlite，以便读取。
- 任何输入的sql都需要SQL parser解析，仅单条select，语法错误给出提示。
- 如果查询不包含limit子句则限制limit 1000。
- sql参数化或严格 AST 检查，禁止sql注入。
- 输出格式是json，前端将其组织成表格显示。

后端使用 Python (uv) / FastAPI / sqlglot / openai sdk 来实现。 
前端使用 React / refine 5 / tailwind / ant design 来实现。
sql editor 使用 monaco editor 来实现。
数据库连接和 metadata 存储在 sqlite 数据库中，放在 ../../db_query.db 中。

后端 API 需要支持 cors，允许所有 origin。大致 API 如下：

```bash
# 获取所有已存储的数据库
GET /api/v1/dbs
# 添加一个数据库
PUT /api/v1/dbs/{name}

{
  "url": "postgres://postgres:postgres@localhost:5432/postgres"
}

# 获取一个数据库的 metadata
GET /api/v1/dbs/{name}

# 查询某个数据库的信息
POST /api/v1/dbs/{name}/query

{
  "sql": "SELECT * FROM users"
}

# 根据自然语言生成 sql
POST /api/v1/dbs/{name}/query/natural

{
  "prompt": "查询用户表的所有信息"
}
```