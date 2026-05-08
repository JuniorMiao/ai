/** POST `/api/v1/dbs/{name}/query` */

const base =
  (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    throw new Error(`Invalid JSON (${res.status})`)
  }
  if (!res.ok) {
    const err = data as { error?: { message?: string } } | null
    const msg = err?.error?.message ?? `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data as T
}

export type QueryResult = {
  columns: string[]
  rows: unknown[][]
  truncated: boolean
  maxRows: number
}

export async function executeQuery(dbName: string, sql: string): Promise<QueryResult> {
  const res = await fetch(
    `${base}/api/v1/dbs/${encodeURIComponent(dbName)}/query`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql }),
    },
  )
  return parseJson<QueryResult>(res)
}
