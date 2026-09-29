CREATE TABLE research_item (
    item_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE brief_version (
    brief_version_id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL,
    release_id TEXT NOT NULL,
    body TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    UNIQUE (brief_id, revision)
);

