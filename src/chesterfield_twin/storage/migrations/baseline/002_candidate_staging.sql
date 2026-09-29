-- New initialization only. Existing 001 stores require future explicit paired recovery/upgrade.
CREATE TABLE staging_run (
    run_id TEXT PRIMARY KEY,
    synthetic INTEGER NOT NULL CHECK (synthetic IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staged_candidate (
    version_id TEXT PRIMARY KEY REFERENCES version(version_id),
    natural_key TEXT NOT NULL,
    source_id TEXT NOT NULL,
    raw_sha256 TEXT NOT NULL REFERENCES artifact(sha256),
    spec_sha256 TEXT NOT NULL REFERENCES artifact(sha256),
    transform_id TEXT NOT NULL
);
CREATE INDEX staged_candidate_by_assertion ON staged_candidate(source_id, natural_key);

CREATE TABLE staging_import (
    import_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES staging_run(run_id),
    retrieval_id TEXT NOT NULL UNIQUE REFERENCES retrieval(retrieval_id),
    source_id TEXT NOT NULL,
    spec_sha256 TEXT NOT NULL REFERENCES artifact(sha256),
    transform_id TEXT NOT NULL,
    candidate_count INTEGER NOT NULL CHECK (candidate_count > 0),
    membership_sha256 TEXT NOT NULL CHECK (length(membership_sha256) = 64),
    issues_json TEXT NOT NULL CHECK (json_valid(issues_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX staging_import_by_run ON staging_import(run_id, import_id);

CREATE TABLE staging_member (
    import_id TEXT NOT NULL REFERENCES staging_import(import_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    version_id TEXT NOT NULL REFERENCES staged_candidate(version_id),
    PRIMARY KEY (import_id, ordinal),
    UNIQUE (import_id, version_id)
);

CREATE TRIGGER staging_member_consistent
BEFORE INSERT ON staging_member
WHEN NOT EXISTS (
    SELECT 1 FROM staging_import i
    JOIN staging_run run ON run.run_id = i.run_id
    JOIN retrieval r ON r.retrieval_id = i.retrieval_id
    JOIN artifact a ON a.artifact_id = r.artifact_id
    JOIN staged_candidate c ON c.version_id = NEW.version_id
    JOIN version v ON v.version_id = c.version_id
    WHERE i.import_id = NEW.import_id AND NEW.ordinal < i.candidate_count
      AND v.synthetic = run.synthetic AND c.source_id = i.source_id
      AND c.spec_sha256 = i.spec_sha256 AND c.raw_sha256 = a.sha256
      AND c.transform_id = i.transform_id
)
BEGIN SELECT RAISE(ABORT, 'inconsistent staged membership'); END;

CREATE TRIGGER immutable_staging_run_update
BEFORE UPDATE ON staging_run
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staging_run_delete
BEFORE DELETE ON staging_run
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staged_candidate_update
BEFORE UPDATE ON staged_candidate
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staged_candidate_delete
BEFORE DELETE ON staged_candidate
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staging_import_update
BEFORE UPDATE ON staging_import
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staging_import_delete
BEFORE DELETE ON staging_import
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staging_member_update
BEFORE UPDATE ON staging_member
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER immutable_staging_member_delete
BEFORE DELETE ON staging_member
BEGIN SELECT RAISE(ABORT, 'staging records are immutable'); END;

CREATE TRIGGER retained_artifact_update
BEFORE UPDATE ON artifact
WHEN EXISTS (SELECT 1 FROM staging_import)
BEGIN SELECT RAISE(ABORT, 'retained metadata is immutable'); END;

CREATE TRIGGER retained_artifact_delete
BEFORE DELETE ON artifact
WHEN EXISTS (SELECT 1 FROM staging_import)
BEGIN SELECT RAISE(ABORT, 'retained metadata is immutable'); END;

CREATE TRIGGER retained_retrieval_update
BEFORE UPDATE ON retrieval
WHEN EXISTS (SELECT 1 FROM staging_import)
BEGIN SELECT RAISE(ABORT, 'retained metadata is immutable'); END;

CREATE TRIGGER retained_retrieval_delete
BEFORE DELETE ON retrieval
WHEN EXISTS (SELECT 1 FROM staging_import)
BEGIN SELECT RAISE(ABORT, 'retained metadata is immutable'); END;
