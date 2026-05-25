CREATE TABLE IF NOT EXISTS log_entries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date   TEXT    NOT NULL,
    raw_text     TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    llm_model    TEXT    NOT NULL DEFAULT 'claude-sonnet-4-6',
    llm_tokens   INTEGER,
    parse_status TEXT    NOT NULL DEFAULT 'ok'
);

CREATE TABLE IF NOT EXISTS tasks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    log_entry_id   INTEGER NOT NULL REFERENCES log_entries(id) ON DELETE CASCADE,
    goal           TEXT    NOT NULL CHECK (goal IN ('phd', 'nl_jobs', 'china_jobs')),
    task_text      TEXT    NOT NULL,
    category       TEXT,
    status         TEXT    NOT NULL DEFAULT 'logged' CHECK (status IN ('logged', 'in_progress', 'done')),
    effort_minutes INTEGER,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_date TEXT    NOT NULL,
    goal         TEXT    NOT NULL CHECK (goal IN ('phd', 'nl_jobs', 'china_jobs')),
    summary_text TEXT    NOT NULL,
    task_count   INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (summary_date, goal)
);

CREATE TABLE IF NOT EXISTS notion_sync (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    notion_page_id TEXT,
    synced_at      TEXT,
    sync_status    TEXT    NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed')),
    error_message  TEXT,
    UNIQUE (task_id)
);

CREATE INDEX IF NOT EXISTS idx_log_entries_date ON log_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_summaries_date   ON daily_summaries(summary_date);
CREATE INDEX IF NOT EXISTS idx_tasks_entry      ON tasks(log_entry_id);
