/** Typed client for `GET/PUT /api/v1/dbs` and metadata (camelCase API). */

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

export type RegisteredDatabaseListItem = {
  name: string
  /** Logical backend: postgres, mysql, … */
  backendKind?: string | null
  createdAt?: string
  updatedAt?: string
}

export type PutDatabaseResponse = {
  name: string
  createdAt: string
}

export type DatabaseMetadataResponse = {
  name: string
  metadata: Record<string, unknown>
  fetchedAt: string
}

export async function listDatabases(): Promise<RegisteredDatabaseListItem[]> {
  const res = await fetch(`${base}/api/v1/dbs`)
  return parseJson<RegisteredDatabaseListItem[]>(res)
}

export async function putDatabase(
  name: string,
  url: string,
  backendKind?: string | null,
): Promise<PutDatabaseResponse> {
  const body: { url: string; backendKind?: string } = { url }
  if (backendKind) body.backendKind = backendKind
  const res = await fetch(`${base}/api/v1/dbs/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson<PutDatabaseResponse>(res)
}

export async function getDatabaseMetadata(name: string): Promise<DatabaseMetadataResponse> {
  const res = await fetch(`${base}/api/v1/dbs/${encodeURIComponent(name)}`)
  return parseJson<DatabaseMetadataResponse>(res)
}

export async function deleteDatabase(name: string): Promise<void> {
  const res = await fetch(`${base}/api/v1/dbs/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  if (res.status === 204) return
  await parseJson<unknown>(res)
}

export async function refreshDatabaseMetadata(name: string): Promise<DatabaseMetadataResponse> {
  const res = await fetch(`${base}/api/v1/dbs/${encodeURIComponent(name)}/refresh`, {
    method: 'POST',
  })
  return parseJson<DatabaseMetadataResponse>(res)
}
