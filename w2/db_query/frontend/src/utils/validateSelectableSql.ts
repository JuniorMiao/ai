/** Client-side PostgreSQL syntax check aligned with backend (single SELECT only). */

import { Parser } from 'node-sql-parser'

const parser = new Parser()

export type SqlValidateResult =
  | { ok: true }
  | { ok: false; message: string }

function flattenStatements(ast: unknown): unknown[] {
  return Array.isArray(ast) ? ast : [ast]
}

export function validateSelectableSql(raw: string): SqlValidateResult {
  const trimmed = raw.trim()
  if (!trimmed) {
    return { ok: false, message: 'SQL 不能为空' }
  }

  let parsed: ReturnType<Parser['parse']>
  try {
    parsed = parser.parse(trimmed, { database: 'postgresql' })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return { ok: false, message: `语法错误：${msg}` }
  }

  const stmts = flattenStatements(parsed.ast)
  if (stmts.length !== 1) {
    return { ok: false, message: '仅允许一条 SQL 语句（单条 SELECT）' }
  }

  const stmt = stmts[0] as { type?: string }
  if (!stmt || stmt.type !== 'select') {
    return { ok: false, message: '仅支持只读 SELECT 查询（与后端策略一致）' }
  }

  return { ok: true }
}
