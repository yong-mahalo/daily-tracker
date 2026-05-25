-- Move goals from hardcoded CHECK constraints / config.json into a real table.
-- Users now define their own goals via the /settings page.

CREATE TABLE IF NOT EXISTS goals (
    key          TEXT PRIMARY KEY,
    label        TEXT NOT NULL,
    color        TEXT NOT NULL,
    description  TEXT,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    notion_db_id TEXT
);

-- Seed three generic placeholders if the table is empty
INSERT INTO goals (key, label, color, sort_order, description)
SELECT 'goal_a', 'Goal A', '#3B82F6', 0, 'First track — edit this label and color in /settings'
WHERE NOT EXISTS (SELECT 1 FROM goals);

INSERT INTO goals (key, label, color, sort_order, description)
SELECT 'goal_b', 'Goal B', '#F97316', 1, 'Second track — edit this label and color in /settings'
WHERE NOT EXISTS (SELECT 1 FROM goals WHERE key = 'goal_b');

INSERT INTO goals (key, label, color, sort_order, description)
SELECT 'goal_c', 'Goal C', '#10B981', 2, 'Third track — edit this label and color in /settings'
WHERE NOT EXISTS (SELECT 1 FROM goals WHERE key = 'goal_c');

-- Backfill: any goal value present in tasks but not in goals (e.g. a previous
-- install with hardcoded 'phd' / 'nl_jobs' / 'china_jobs' rows) gets a row so
-- existing data stays attached to a real goal.
INSERT OR IGNORE INTO goals (key, label, color, sort_order)
SELECT DISTINCT goal, goal, '#888888', 99 FROM tasks;

-- Drop the CHECK constraints on tasks.goal and daily_summaries.goal.
-- SQLite has no ALTER TABLE DROP CHECK, so we rebuild the tables.

CREATE TABLE tasks_new (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    log_entry_id   INTEGER NOT NULL REFERENCES log_entries(id) ON DELETE CASCADE,
    goal           TEXT    NOT NULL,
    task_text      TEXT    NOT NULL,
    category       TEXT,
    status         TEXT    NOT NULL DEFAULT 'logged' CHECK (status IN ('logged', 'in_progress', 'done')),
    effort_minutes INTEGER,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO tasks_new (id, log_entry_id, goal, task_text, category, status, effort_minutes, created_at)
SELECT id, log_entry_id, goal, task_text, category, status, effort_minutes, created_at FROM tasks;
DROP TABLE tasks;
ALTER TABLE tasks_new RENAME TO tasks;
CREATE INDEX IF NOT EXISTS idx_tasks_entry ON tasks(log_entry_id);

CREATE TABLE daily_summaries_new (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_date TEXT    NOT NULL,
    goal         TEXT    NOT NULL,
    summary_text TEXT    NOT NULL,
    task_count   INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (summary_date, goal)
);
INSERT INTO daily_summaries_new (id, summary_date, goal, summary_text, task_count, updated_at)
SELECT id, summary_date, goal, summary_text, task_count, updated_at FROM daily_summaries;
DROP TABLE daily_summaries;
ALTER TABLE daily_summaries_new RENAME TO daily_summaries;
CREATE INDEX IF NOT EXISTS idx_summaries_date ON daily_summaries(summary_date);
