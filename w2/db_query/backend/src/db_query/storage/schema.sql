-- Local SQLite for db_query (see specs data-model.md)

CREATE TABLE IF NOT EXISTS registered_database (
    name TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS database_metadata (
    db_name TEXT PRIMARY KEY REFERENCES registered_database (name) ON DELETE CASCADE,
    payload_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    schema_version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS llm_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    api_key_ref TEXT,
    model TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0
);
