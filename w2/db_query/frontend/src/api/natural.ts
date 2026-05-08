/** `/api/v1/llm-settings`, `/api/v1/dbs/{name}/query/natural` */

const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

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

export type LlmSettings = {
  id: number
  provider: string
  baseUrl: string
  model: string
  apiKeyRef: string | null
  hasApiKey: boolean
  isDefault: boolean
}

export type LlmSettingsListResponse = {
  items: LlmSettings[]
  defaultId: number | null
  hasResolvableKey: boolean
}

export async function listLlmSettings(): Promise<LlmSettingsListResponse> {
  const res = await fetch(`${base}/api/v1/llm-settings`)
  return parseJson<LlmSettingsListResponse>(res)
}

export type LlmProviderCatalogItem = {
  id: string
  displayName: string
  shortName: string
  defaultBaseUrl: string
  defaultModel: string
  primaryApiKeyEnv: string
  passwordPlaceholder: string
  apiKeyInlineHint: string
}

export type LlmProviderCatalogResponse = {
  items: LlmProviderCatalogItem[]
}

/** Vendor list from backend registry (`LLM_PROVIDER_SPECS`) for dropdowns and defaults. */
export async function listLlmProviders(): Promise<LlmProviderCatalogResponse> {
  const res = await fetch(`${base}/api/v1/llm-providers`)
  return parseJson<LlmProviderCatalogResponse>(res)
}

export type PostLlmSettingsBody = {
  provider?: string
  baseUrl: string
  model: string
  apiKeyRef?: string | null
  apiKey?: string | null
  setAsDefault?: boolean
}

export async function createLlmSettings(body: PostLlmSettingsBody): Promise<LlmSettings> {
  const res = await fetch(`${base}/api/v1/llm-settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson<LlmSettings>(res)
}

export type PutLlmSettingsBody = {
  provider?: string
  baseUrl: string
  model: string
  apiKeyRef?: string | null
  apiKey?: string | null
}

export async function updateLlmSettings(
  profileId: number,
  body: PutLlmSettingsBody,
): Promise<LlmSettings> {
  const res = await fetch(`${base}/api/v1/llm-settings/${profileId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson<LlmSettings>(res)
}

export async function deleteLlmSettings(profileId: number): Promise<void> {
  const res = await fetch(`${base}/api/v1/llm-settings/${profileId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const text = await res.text()
    let data: unknown
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      throw new Error(`HTTP ${res.status}`)
    }
    const err = data as { error?: { message?: string } } | null
    throw new Error(err?.error?.message ?? `HTTP ${res.status}`)
  }
}

export async function setDefaultLlmProfile(profileId: number): Promise<LlmSettings> {
  const res = await fetch(`${base}/api/v1/llm-settings/${profileId}/default`, {
    method: 'POST',
  })
  return parseJson<LlmSettings>(res)
}

export type NaturalQueryResponse = {
  sql: string
  warnings: string[]
}

export async function naturalQuery(
  dbName: string,
  prompt: string,
  llmSettingsId?: number | null,
): Promise<NaturalQueryResponse> {
  const body: Record<string, unknown> = { prompt }
  if (llmSettingsId != null) {
    body.llmSettingsId = llmSettingsId
  }
  const res = await fetch(
    `${base}/api/v1/dbs/${encodeURIComponent(dbName)}/query/natural`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  )
  return parseJson<NaturalQueryResponse>(res)
}
