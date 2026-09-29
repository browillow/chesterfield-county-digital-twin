CREATE TABLE version (
    version_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (length(kind) > 0),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    synthetic INTEGER NOT NULL DEFAULT 0 CHECK (synthetic IN (0, 1)),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE release (
    release_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('draft', 'sealed')),
    manifest_json TEXT NOT NULL CHECK (json_valid(manifest_json)),
    sealed_at TEXT,
    CHECK ((status = 'draft' AND sealed_at IS NULL) OR (status = 'sealed' AND sealed_at IS NOT NULL))
);

CREATE TABLE release_version (
    release_id TEXT NOT NULL REFERENCES release(release_id),
    version_id TEXT NOT NULL REFERENCES version(version_id),
    PRIMARY KEY (release_id, version_id)
);
CREATE INDEX release_version_by_version ON release_version(version_id, release_id);

CREATE TABLE version_link (
    from_version_id TEXT NOT NULL REFERENCES version(version_id),
    to_version_id TEXT NOT NULL REFERENCES version(version_id),
    role TEXT NOT NULL CHECK (length(trim(role)) > 0),
    PRIMARY KEY (from_version_id, to_version_id, role),
    CHECK (from_version_id <> to_version_id)
);
CREATE INDEX version_link_by_target ON version_link(to_version_id, from_version_id);

CREATE TABLE app_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    active_release_id TEXT REFERENCES release(release_id)
);
INSERT INTO app_state(singleton, active_release_id) VALUES (1, NULL);

CREATE TABLE artifact (
    artifact_id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE CHECK (length(sha256) = 64),
    byte_length INTEGER NOT NULL CHECK (byte_length >= 0),
    media_type TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retrieval (
    retrieval_id TEXT PRIMARY KEY,
    artifact_id TEXT REFERENCES artifact(artifact_id),
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json))
);

CREATE TABLE measurement (
    measurement_id TEXT PRIMARY KEY,
    claim_class TEXT NOT NULL CHECK (claim_class IN ('reported', 'calculated', 'inference', 'hypothesis', 'scenario')),
    value_state TEXT NOT NULL CHECK (value_state IN ('observed', 'suppressed', 'unavailable', 'not_applicable')),
    value TEXT,
    reason TEXT,
    unit TEXT NOT NULL,
    universe TEXT NOT NULL,
    geography_id TEXT NOT NULL,
    geography_vintage TEXT NOT NULL,
    reference_period TEXT NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 0 CHECK (synthetic IN (0, 1)),
    CHECK (
        (value_state = 'observed' AND value IS NOT NULL)
        OR (value_state <> 'observed' AND value IS NULL
            AND reason IS NOT NULL AND length(trim(reason)) > 0)
    )
);

CREATE TRIGGER sealed_version_link_insert
BEFORE INSERT ON version_link
WHEN EXISTS (
    SELECT 1 FROM release_version rv JOIN release r ON r.release_id = rv.release_id
    WHERE rv.version_id = NEW.from_version_id AND r.status = 'sealed'
)
BEGIN SELECT RAISE(ABORT, 'sealed version links are immutable'); END;

CREATE TRIGGER sealed_version_link_update
BEFORE UPDATE ON version_link
WHEN EXISTS (
    SELECT 1 FROM release_version rv JOIN release r ON r.release_id = rv.release_id
    WHERE rv.version_id IN (OLD.from_version_id, NEW.from_version_id) AND r.status = 'sealed'
)
BEGIN SELECT RAISE(ABORT, 'sealed version links are immutable'); END;

CREATE TRIGGER sealed_version_link_delete
BEFORE DELETE ON version_link
WHEN EXISTS (
    SELECT 1 FROM release_version rv JOIN release r ON r.release_id = rv.release_id
    WHERE rv.version_id = OLD.from_version_id AND r.status = 'sealed'
)
BEGIN SELECT RAISE(ABORT, 'sealed version links are immutable'); END;

CREATE TRIGGER sealed_release_version_insert
BEFORE INSERT ON release_version
WHEN (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release membership is immutable'); END;

CREATE TRIGGER sealed_release_version_update
BEFORE UPDATE ON release_version
WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
  OR (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release membership is immutable'); END;

CREATE TRIGGER sealed_release_version_delete
BEFORE DELETE ON release_version
WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release membership is immutable'); END;

CREATE TRIGGER sealed_version_update
BEFORE UPDATE ON version
BEGIN SELECT RAISE(ABORT, 'version content is immutable'); END;

CREATE TRIGGER sealed_version_delete
BEFORE DELETE ON version
BEGIN SELECT RAISE(ABORT, 'version content is immutable'); END;

CREATE TRIGGER sealed_release_update
BEFORE UPDATE ON release
WHEN OLD.status = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release is immutable'); END;

CREATE TRIGGER sealed_release_delete
BEFORE DELETE ON release
WHEN OLD.status = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release is immutable'); END;

CREATE TRIGGER active_release_must_be_sealed_insert
BEFORE INSERT ON app_state
WHEN NEW.active_release_id IS NOT NULL
 AND (SELECT status FROM release WHERE release_id = NEW.active_release_id) <> 'sealed'
BEGIN SELECT RAISE(ABORT, 'active release must be sealed'); END;

CREATE TRIGGER active_release_must_be_sealed_update
BEFORE UPDATE OF active_release_id ON app_state
WHEN NEW.active_release_id IS NOT NULL
 AND (SELECT status FROM release WHERE release_id = NEW.active_release_id) <> 'sealed'
BEGIN SELECT RAISE(ABORT, 'active release must be sealed'); END;
