-- T007b fresh initialization only. Earlier ledgers are never upgraded in place.
CREATE TABLE release_build_report (
    report_id TEXT PRIMARY KEY CHECK (length(report_id) = 64),
    run_id TEXT NOT NULL REFERENCES staging_run(run_id),
    candidate_report_id TEXT NOT NULL REFERENCES candidate_validation_report(report_id),
    content_id TEXT,
    valid INTEGER NOT NULL CHECK (valid IN (0, 1)),
    content_json TEXT NOT NULL CHECK (json_valid(content_json)),
    object_sha256 TEXT NOT NULL REFERENCES artifact(sha256),
    CHECK (valid = 0 OR (content_id IS NOT NULL AND length(content_id) = 64))
);
CREATE TABLE release_closure (
    release_id TEXT PRIMARY KEY REFERENCES release(release_id),
    run_id TEXT NOT NULL REFERENCES staging_run(run_id),
    candidate_report_id TEXT NOT NULL REFERENCES candidate_validation_report(report_id),
    build_report_id TEXT NOT NULL REFERENCES release_build_report(report_id),
    manifest_sha256 TEXT NOT NULL REFERENCES artifact(sha256),
    content_id TEXT NOT NULL CHECK (length(content_id) = 64)
);
CREATE TABLE release_import (
    release_id TEXT NOT NULL REFERENCES release(release_id),
    import_id TEXT NOT NULL REFERENCES staging_import(import_id),
    PRIMARY KEY (release_id, import_id)
);
CREATE TABLE release_dependency (
    release_id TEXT NOT NULL REFERENCES release(release_id),
    node_id TEXT NOT NULL CHECK (length(node_id) = 64),
    kind TEXT NOT NULL,
    node_key TEXT NOT NULL,
    node_json TEXT NOT NULL CHECK (json_valid(node_json)),
    PRIMARY KEY (release_id, node_id),
    UNIQUE (release_id, kind, node_key),
    CHECK (json_extract(node_json, '$.kind') IS kind),
    CHECK (json_extract(node_json, '$.key') IS node_key)
);
CREATE TABLE release_edge (
    release_id TEXT NOT NULL REFERENCES release(release_id),
    from_node TEXT NOT NULL,
    role TEXT NOT NULL CHECK (length(role) > 0),
    to_node TEXT NOT NULL,
    PRIMARY KEY (release_id, from_node, role, to_node),
    FOREIGN KEY (release_id, from_node) REFERENCES release_dependency(release_id, node_id),
    FOREIGN KEY (release_id, to_node) REFERENCES release_dependency(release_id, node_id)
);
CREATE TRIGGER no_direct_sealed_release
BEFORE INSERT ON release WHEN NEW.status = 'sealed'
BEGIN SELECT RAISE(ABORT, 'release must be assembled before sealing'); END;

CREATE TRIGGER complete_release_before_seal
BEFORE UPDATE OF status ON release WHEN NEW.status = 'sealed'
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM release_closure c
        JOIN release_build_report b ON b.report_id = c.build_report_id
        JOIN candidate_validation_report v ON v.report_id = c.candidate_report_id
        JOIN staging_run run ON run.run_id = c.run_id
        WHERE c.release_id = NEW.release_id AND b.valid = 1
          AND b.run_id = c.run_id AND v.run_id = c.run_id
          AND b.candidate_report_id = c.candidate_report_id
          AND b.content_id = c.content_id
          AND json_extract(NEW.manifest_json, '$.report_id') = b.report_id
          AND json_extract(NEW.manifest_json, '$.content.contract') = 'first-slice-release/1'
          AND json_extract(NEW.manifest_json, '$.content.selection.run_id') = c.run_id
          AND json_extract(NEW.manifest_json, '$.content.synthetic') = run.synthetic
          AND json_extract(NEW.manifest_json,
                           '$.content.selection.candidate_report_id') = v.report_id
          AND json_extract(b.content_json, '$.content_id') = c.content_id
          AND json_extract(b.content_json, '$.run_id') = c.run_id
          AND json_extract(b.content_json, '$.candidate_report_id') = v.report_id
          AND json_extract(b.content_json, '$.synthetic') = run.synthetic
          AND NOT EXISTS (SELECT 1 FROM json_each(b.content_json, '$.issues')
                          WHERE json_extract(value, '$.severity') = 'error')
          AND json_array_length(v.content_json, '$.inputs') = 3
          AND json_extract(v.content_json, '$.synthetic') = run.synthetic
          AND NOT EXISTS (SELECT 1 FROM json_each(v.content_json, '$.issues')
                          WHERE json_extract(value, '$.severity') = 'error')
          AND NOT EXISTS (SELECT 1 FROM json_each(v.content_json, '$.inputs')
                          WHERE json_extract(value, '$.verified') IS NOT 1)
    ) THEN RAISE(ABORT, 'release requires a bound successful closure report') END;
    SELECT CASE WHEN
        (SELECT count(*) FROM release_import WHERE release_id = NEW.release_id) <> 3
        OR (SELECT count(*) FROM release_version WHERE release_id = NEW.release_id) <> 303
        OR json_array_length(NEW.manifest_json, '$.content.selection.import_ids') IS NOT 3
        OR json_array_length(NEW.manifest_json, '$.content.selection.version_ids') IS NOT 303
        OR EXISTS (SELECT 1 FROM release_import ri JOIN staging_import i USING(import_id)
                   JOIN release_closure c ON c.release_id = ri.release_id
                   WHERE ri.release_id = NEW.release_id AND i.run_id <> c.run_id)
    THEN RAISE(ABORT, 'release selection is incomplete') END;
    SELECT CASE WHEN EXISTS (
        SELECT import_id FROM release_import WHERE release_id = NEW.release_id
        EXCEPT SELECT value FROM json_each(NEW.manifest_json, '$.content.selection.import_ids')
    ) OR EXISTS (
        SELECT value FROM json_each(NEW.manifest_json, '$.content.selection.import_ids')
        EXCEPT SELECT import_id FROM release_import WHERE release_id = NEW.release_id
    ) THEN RAISE(ABORT, 'release manifest membership differs') END;
    SELECT CASE WHEN EXISTS (
        SELECT version_id FROM release_version WHERE release_id = NEW.release_id
        EXCEPT SELECT value FROM json_each(NEW.manifest_json, '$.content.selection.version_ids')
    ) OR EXISTS (
        SELECT value FROM json_each(NEW.manifest_json, '$.content.selection.version_ids')
        EXCEPT SELECT version_id FROM release_version WHERE release_id = NEW.release_id
    ) THEN RAISE(ABORT, 'release manifest membership differs') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM release_closure c
        JOIN release_build_report b ON b.report_id = c.build_report_id
        JOIN candidate_validation_report v ON v.report_id = c.candidate_report_id
        WHERE c.release_id = NEW.release_id
          AND json_extract(b.content_json, '$.import_ids') =
              json_extract(NEW.manifest_json, '$.content.selection.import_ids')
          AND NOT EXISTS (
              SELECT import_id FROM release_import WHERE release_id = NEW.release_id
              EXCEPT SELECT json_extract(value, '$.import_id')
                     FROM json_each(v.content_json, '$.inputs')
          )
          AND NOT EXISTS (
              SELECT 1 FROM json_each(v.content_json, '$.inputs') input
              JOIN staging_import i ON i.import_id = json_extract(input.value, '$.import_id')
              WHERE json_extract(input.value, '$.run_id') IS NOT c.run_id
                 OR json_extract(input.value, '$.retrieval_id') IS NOT i.retrieval_id
                 OR json_extract(input.value, '$.source_id') IS NOT i.source_id
                 OR json_extract(input.value, '$.spec_sha256') IS NOT i.spec_sha256
                 OR json_extract(input.value, '$.transform_id') IS NOT i.transform_id
                 OR json_extract(input.value, '$.membership_sha256') IS NOT i.membership_sha256
          )
    ) THEN RAISE(ABORT, 'release report selection differs') END;
    SELECT CASE WHEN
        (SELECT count(*) FROM release_version rv JOIN version v USING(version_id)
         WHERE rv.release_id = NEW.release_id AND v.kind = 'observation') <> 225
        OR (SELECT count(*) FROM release_version rv JOIN version v USING(version_id)
            WHERE rv.release_id = NEW.release_id AND v.kind = 'boundary') <> 75
        OR (SELECT count(*) FROM release_version rv JOIN version v USING(version_id)
            WHERE rv.release_id = NEW.release_id AND v.kind = 'document_excerpt') <> 3
    THEN RAISE(ABORT, 'release candidate kinds are incomplete') END;
    SELECT CASE WHEN EXISTS (
        SELECT m.version_id FROM staging_member m JOIN release_import i USING(import_id)
        WHERE i.release_id = NEW.release_id
        EXCEPT SELECT version_id FROM release_version WHERE release_id = NEW.release_id
    ) OR EXISTS (
        SELECT version_id FROM release_version WHERE release_id = NEW.release_id
        EXCEPT SELECT m.version_id FROM staging_member m JOIN release_import i USING(import_id)
        WHERE i.release_id = NEW.release_id
    ) THEN RAISE(ABORT, 'release omits selected candidate membership') END;
    SELECT CASE WHEN
        (SELECT count(*) FROM release_dependency WHERE release_id = NEW.release_id)
          IS NOT json_array_length(NEW.manifest_json, '$.content.nodes')
        OR EXISTS (
            SELECT json(node_json) FROM release_dependency WHERE release_id = NEW.release_id
            EXCEPT SELECT json(value) FROM json_each(NEW.manifest_json, '$.content.nodes')
        ) OR EXISTS (
            SELECT json(value) FROM json_each(NEW.manifest_json, '$.content.nodes')
            EXCEPT SELECT json(node_json) FROM release_dependency WHERE release_id = NEW.release_id
        )
        OR (SELECT count(*) FROM release_dependency
            WHERE release_id = NEW.release_id AND kind = 'candidate') <> 303
        OR EXISTS (
            SELECT node_key FROM release_dependency
            WHERE release_id = NEW.release_id AND kind = 'candidate'
            EXCEPT SELECT version_id FROM release_version WHERE release_id = NEW.release_id
        )
    THEN RAISE(ABORT, 'release dependency membership differs') END;
    SELECT CASE WHEN
        (SELECT count(*) FROM release_edge WHERE release_id = NEW.release_id)
          IS NOT json_array_length(NEW.manifest_json, '$.content.edges')
        OR EXISTS (
            SELECT from_node, role, to_node FROM release_edge WHERE release_id = NEW.release_id
            EXCEPT SELECT json_extract(value, '$.from_node'), json_extract(value, '$.role'),
                          json_extract(value, '$.to_node')
            FROM json_each(NEW.manifest_json, '$.content.edges')
        ) OR EXISTS (
            SELECT json_extract(value, '$.from_node'), json_extract(value, '$.role'),
                   json_extract(value, '$.to_node')
            FROM json_each(NEW.manifest_json, '$.content.edges')
            EXCEPT SELECT from_node, role, to_node FROM release_edge WHERE release_id = NEW.release_id
        )
    THEN RAISE(ABORT, 'release edge membership differs') END;
    SELECT CASE WHEN EXISTS (
        SELECT kind FROM (
            SELECT 'raw' AS kind UNION SELECT 'spec' UNION SELECT 'retrieval' UNION SELECT 'source'
            UNION SELECT 'metric' UNION SELECT 'document' UNION SELECT 'transform' UNION SELECT 'query'
            UNION SELECT 'config' UNION SELECT 'dependency' UNION SELECT 'code' UNION SELECT 'schema'
            UNION SELECT 'coverage'
        ) EXCEPT SELECT kind FROM release_dependency WHERE release_id = NEW.release_id
    ) THEN RAISE(ABORT, 'release supporting categories are incomplete') END;
END;

CREATE TRIGGER sealed_release_closure_insert
BEFORE INSERT ON release_closure WHEN (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_closure_update
BEFORE UPDATE ON release_closure WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed' OR (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_closure_delete
BEFORE DELETE ON release_closure WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_import_insert
BEFORE INSERT ON release_import WHEN (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_import_update
BEFORE UPDATE ON release_import WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed' OR (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_import_delete
BEFORE DELETE ON release_import WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_dependency_insert
BEFORE INSERT ON release_dependency WHEN (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_dependency_update
BEFORE UPDATE ON release_dependency WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed' OR (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_dependency_delete
BEFORE DELETE ON release_dependency WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_edge_insert
BEFORE INSERT ON release_edge WHEN (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_edge_update
BEFORE UPDATE ON release_edge WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed' OR (SELECT status FROM release WHERE release_id = NEW.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER sealed_release_edge_delete
BEFORE DELETE ON release_edge WHEN (SELECT status FROM release WHERE release_id = OLD.release_id) = 'sealed'
BEGIN SELECT RAISE(ABORT, 'sealed release support is immutable'); END;

CREATE TRIGGER immutable_release_build_report_update
BEFORE UPDATE ON release_build_report
BEGIN SELECT RAISE(ABORT, 'release build reports are immutable'); END;

CREATE TRIGGER immutable_release_build_report_delete
BEFORE DELETE ON release_build_report
BEGIN SELECT RAISE(ABORT, 'release build reports are immutable'); END;

-- REPLACE deletes conflicting rows without DELETE triggers unless recursive triggers
-- are enabled. Never rely on that connection setting to protect sealed evidence.
CREATE TRIGGER no_replace_sealed_release
BEFORE INSERT ON release
WHEN EXISTS (SELECT 1 FROM release WHERE release_id = NEW.release_id AND status = 'sealed')
BEGIN SELECT RAISE(ABORT, 'sealed release is immutable'); END;

CREATE TRIGGER no_replace_version
BEFORE INSERT ON version
WHEN EXISTS (SELECT 1 FROM version WHERE version_id = NEW.version_id)
BEGIN SELECT RAISE(ABORT, 'immutable evidence cannot be replaced'); END;

CREATE TRIGGER no_replace_staging_run
BEFORE INSERT ON staging_run
WHEN EXISTS (SELECT 1 FROM staging_run WHERE run_id = NEW.run_id)
BEGIN SELECT RAISE(ABORT, 'immutable evidence cannot be replaced'); END;

CREATE TRIGGER no_replace_staged_candidate
BEFORE INSERT ON staged_candidate
WHEN EXISTS (SELECT 1 FROM staged_candidate WHERE version_id = NEW.version_id)
BEGIN SELECT RAISE(ABORT, 'immutable evidence cannot be replaced'); END;

CREATE TRIGGER no_replace_staging_import
BEFORE INSERT ON staging_import
WHEN EXISTS (SELECT 1 FROM staging_import WHERE import_id = NEW.import_id)
BEGIN SELECT RAISE(ABORT, 'immutable evidence cannot be replaced'); END;

CREATE TRIGGER no_replace_staging_member
BEFORE INSERT ON staging_member
WHEN EXISTS (SELECT 1 FROM staging_member WHERE import_id = NEW.import_id
             AND (ordinal = NEW.ordinal OR version_id = NEW.version_id))
BEGIN SELECT RAISE(ABORT, 'immutable evidence cannot be replaced'); END;

CREATE TRIGGER no_conflicting_replace_artifact
BEFORE INSERT ON artifact
WHEN EXISTS (SELECT 1 FROM artifact WHERE (artifact_id = NEW.artifact_id OR sha256 = NEW.sha256) AND (artifact_id IS NOT NEW.artifact_id OR sha256 IS NOT NEW.sha256 OR byte_length IS NOT NEW.byte_length OR media_type IS NOT NEW.media_type))
BEGIN SELECT RAISE(ABORT, 'immutable evidence conflicts with retained identity'); END;

CREATE TRIGGER no_conflicting_replace_retrieval
BEFORE INSERT ON retrieval
WHEN EXISTS (SELECT 1 FROM retrieval WHERE retrieval_id = NEW.retrieval_id AND (retrieval_id IS NOT NEW.retrieval_id OR artifact_id IS NOT NEW.artifact_id OR source_url IS NOT NEW.source_url OR retrieved_at IS NOT NEW.retrieved_at OR outcome IS NOT NEW.outcome OR metadata_json IS NOT NEW.metadata_json))
BEGIN SELECT RAISE(ABORT, 'immutable evidence conflicts with retained identity'); END;

CREATE TRIGGER no_conflicting_replace_candidate_validation_report
BEFORE INSERT ON candidate_validation_report
WHEN EXISTS (SELECT 1 FROM candidate_validation_report WHERE report_id = NEW.report_id AND (report_id IS NOT NEW.report_id OR run_id IS NOT NEW.run_id OR content_json IS NOT NEW.content_json))
BEGIN SELECT RAISE(ABORT, 'immutable evidence conflicts with retained identity'); END;

CREATE TRIGGER no_conflicting_replace_release_build_report
BEFORE INSERT ON release_build_report
WHEN EXISTS (SELECT 1 FROM release_build_report WHERE report_id = NEW.report_id AND (report_id IS NOT NEW.report_id OR run_id IS NOT NEW.run_id OR candidate_report_id IS NOT NEW.candidate_report_id OR content_id IS NOT NEW.content_id OR valid IS NOT NEW.valid OR content_json IS NOT NEW.content_json OR object_sha256 IS NOT NEW.object_sha256))
BEGIN SELECT RAISE(ABORT, 'immutable evidence conflicts with retained identity'); END;
