-- Fresh initialization only; no silent upgrade of earlier stores.
CREATE TABLE candidate_validation_report (
    report_id TEXT PRIMARY KEY CHECK (length(report_id) = 64),
    run_id TEXT NOT NULL REFERENCES staging_run(run_id),
    content_json TEXT NOT NULL CHECK (json_valid(content_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX candidate_validation_by_run ON candidate_validation_report(run_id, report_id);
CREATE TRIGGER immutable_candidate_validation_update
BEFORE UPDATE ON candidate_validation_report
BEGIN SELECT RAISE(ABORT, 'validation reports are immutable'); END;
CREATE TRIGGER immutable_candidate_validation_delete
BEFORE DELETE ON candidate_validation_report
BEGIN SELECT RAISE(ABORT, 'validation reports are immutable'); END;
