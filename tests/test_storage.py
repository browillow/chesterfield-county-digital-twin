import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

import chesterfield_twin.storage as storage_module
from chesterfield_twin.domain.contracts import Measurement
from chesterfield_twin.storage import (
    ArtifactStore,
    BaselineRepository,
    MigrationError,
    PrivateRepository,
    StorageBusyError,
    StorageError,
    check_initialized,
    initialize,
    insert_measurement,
    maintenance_lock,
)


def connect(root: Path, database: str = "baseline.sqlite") -> sqlite3.Connection:
    connection = sqlite3.connect(root / database)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def test_initialize_is_idempotent_secure_and_checks_both_stores(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    initialize(root)
    check_initialized(root)

    assert (root / "baseline.sqlite").is_file()
    assert (root / "private" / "strategy.sqlite").is_file()
    assert os.stat(root).st_mode & 0o777 == 0o700
    assert os.stat(root / "baseline.sqlite").st_mode & 0o777 == 0o600
    assert os.stat(root / "private" / "strategy.sqlite").st_mode & 0o777 == 0o600
    assert BaselineRepository(root).bootstrap().model_dump() == {
        "api_version": "v1",
        "active_release_id": None,
        "has_baseline": False,
        "capabilities": [],
    }


def test_maintenance_lock_excludes_initializer_but_allows_shared_holders(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    with maintenance_lock(root, exclusive=False):
        with maintenance_lock(root, exclusive=False):
            check_initialized(root)
        with pytest.raises(StorageBusyError):
            initialize(root)


def test_partial_pair_and_changed_or_unknown_migration_fail_closed(tmp_path):
    partial = tmp_path / "partial"
    initialize(partial)
    (partial / "private" / "strategy.sqlite").unlink()
    with pytest.raises(MigrationError, match="complete pair"):
        initialize(partial)

    root = tmp_path / "changed"
    initialize(root)
    with connect(root) as connection:
        connection.execute("UPDATE schema_migration SET checksum = 'tampered'")
    with pytest.raises(MigrationError, match="unknown or has changed"):
        check_initialized(root)

    root2 = tmp_path / "unknown"
    initialize(root2)
    with connect(root2) as connection:
        connection.execute(
            "INSERT INTO schema_migration VALUES ('999_future.sql', 'future-checksum')"
        )
    with pytest.raises(MigrationError, match="unknown or has changed"):
        initialize(root2)


def test_foreign_keys_and_measurement_states(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    common = {
        "claim_class": "reported",
        "unit": "people",
        "universe": "Synthetic test population",
        "geography_id": "051",
        "geography_vintage": "2024",
        "reference_period": "2024",
        "synthetic": True,
    }
    with connect(root) as connection:
        insert_measurement(
            connection,
            "zero",
            Measurement(**common, value_state="observed", value="0"),
        )
        insert_measurement(
            connection,
            "withheld",
            Measurement(**common, value_state="suppressed", reason="Synthetic suppression"),
        )
        rows = connection.execute(
            "SELECT measurement_id, value_state, value, reason FROM measurement ORDER BY measurement_id"
        ).fetchall()
        assert rows == [
            ("withheld", "suppressed", None, "Synthetic suppression"),
            ("zero", "observed", "0", None),
        ]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO release_version(release_id, version_id) VALUES ('missing', 'missing')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO measurement "
                "(measurement_id, claim_class, value_state, value, reason, unit, universe, "
                "geography_id, geography_vintage, reference_period, synthetic) "
                "VALUES ('bad', 'reported', 'unavailable', NULL, NULL, 'people', "
                "'Synthetic test population', '051', '2024', '2024', 1)"
            )
        connection.execute(
            "INSERT INTO measurement "
            "(measurement_id, claim_class, value_state, value, reason, unit, universe, "
            "geography_id, geography_vintage, reference_period, synthetic) "
            "VALUES ('observed-note', 'reported', 'observed', '1', 'Source annotation', "
            "'people', 'Synthetic test population', '051', '2024', '2024', 1)"
        )


def test_sealed_membership_and_version_content_are_immutable(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    with connect(root) as connection:
        connection.execute(
            "INSERT INTO version(version_id, kind, payload_json, synthetic) VALUES (?, ?, ?, 1)",
            ("v1", "synthetic_test", json.dumps({"label": "synthetic public record"})),
        )
        connection.execute(
            "INSERT INTO version(version_id, kind, payload_json, synthetic) VALUES (?, ?, ?, 1)",
            ("v2", "synthetic_evidence", json.dumps({"label": "synthetic evidence"})),
        )
        connection.execute("INSERT INTO version_link VALUES ('v1', 'v2', 'evidence')")
        connection.execute(
            "INSERT INTO release(release_id, status, manifest_json) VALUES ('r1', 'draft', '{}')"
        )
        connection.execute("INSERT INTO release_version VALUES ('r1', 'v1')")
        connection.execute(
            "UPDATE release SET status = 'sealed', sealed_at = '2026-09-27T00:00:00Z' "
            "WHERE release_id = 'r1'"
        )
        for statement in (
            "UPDATE version SET payload_json = '{}' WHERE version_id = 'v1'",
            "DELETE FROM version WHERE version_id = 'v1'",
            "DELETE FROM release_version WHERE release_id = 'r1' AND version_id = 'v1'",
            "INSERT INTO release_version VALUES ('r1', 'v1')",
            "DELETE FROM version_link WHERE from_version_id = 'v1'",
            "UPDATE version_link SET role = 'support' WHERE from_version_id = 'v1'",
            "INSERT INTO version_link VALUES ('v1', 'v2', 'support')",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement)


def test_export_requires_explicit_sealed_release_and_excludes_private_data(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    private_sentinel = "PRIVATE-SYNTHETIC-SENTINEL-93F1"
    PrivateRepository(root).add_research_item("private-1", private_sentinel)
    with connect(root) as connection:
        connection.execute(
            "INSERT INTO version(version_id, kind, payload_json, synthetic) VALUES (?, ?, ?, 1)",
            ("v-public", "synthetic_test", json.dumps({"label": "public synthetic"})),
        )
        connection.execute("INSERT INTO release VALUES ('draft-release', 'draft', '{}', NULL)")
        connection.execute(
            "INSERT INTO release VALUES ('sealed-release', 'draft', ?, NULL)",
            (json.dumps({"fixture": "synthetic"}),),
        )
        connection.execute("INSERT INTO release_version VALUES ('sealed-release', 'v-public')")
        connection.execute(
            "UPDATE release SET status = 'sealed', sealed_at = '2026-09-27T00:00:00Z' "
            "WHERE release_id = 'sealed-release'"
        )
    repository = BaselineRepository(root)
    for release_id in ("draft-release", "unknown-release"):
        with pytest.raises(StorageError, match="unknown or not sealed"):
            repository.export_release(release_id)
    exported = repository.export_release("sealed-release")
    assert exported["release_id"] == "sealed-release"
    assert private_sentinel not in json.dumps(exported)


def test_artifacts_are_content_addressed_and_unsafe_paths_are_rejected(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    store = ArtifactStore(root)
    content = b"synthetic artifact bytes"
    digest = store.put(content)
    assert digest == hashlib.sha256(content).hexdigest()
    assert store.put(content) == digest
    assert store.path(digest).read_bytes() == content
    assert os.stat(store.path(digest)).st_mode & 0o777 == 0o600
    for unsafe in ("../baseline.sqlite", "/etc/passwd", digest.upper()):
        with pytest.raises(StorageError, match="invalid artifact digest"):
            store.path(unsafe)
    with pytest.raises(StorageError, match="does not exist"):
        store.path("a" * 64)


def test_symlinked_managed_path_is_rejected(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "objects").symlink_to(outside, target_is_directory=True)
    with pytest.raises(StorageError, match="symlink"):
        initialize(root)


def test_dangling_and_intermediate_artifact_symlinks_are_rejected(tmp_path):
    dangling_root = tmp_path / "dangling-root"
    dangling_root.symlink_to(tmp_path / "missing", target_is_directory=True)
    with pytest.raises(StorageError, match="symlink"):
        initialize(dangling_root)

    root = tmp_path / "data"
    initialize(root)
    digest = hashlib.sha256(b"synthetic").hexdigest()
    prefix = root / "objects" / "sha256" / digest[:2]
    prefix.symlink_to(tmp_path / "missing-prefix", target_is_directory=True)
    with pytest.raises(StorageError, match="symlink"):
        ArtifactStore(root).put(b"synthetic")
    with pytest.raises(StorageError, match="symlink"):
        ArtifactStore(root).path(digest)


def test_failed_initial_migration_never_creates_an_accepted_pair(tmp_path, monkeypatch):
    root = tmp_path / "data"
    original = storage_module._expected_migrations

    def broken(database):
        if database == "baseline":
            return [("001_broken.sql", "synthetic-checksum", "CREATE TABLE partial(x);\nBOGUS")]
        return original(database)

    monkeypatch.setattr(storage_module, "_expected_migrations", broken)
    with pytest.raises((sqlite3.Error, MigrationError)):
        initialize(root)
    with pytest.raises(MigrationError):
        check_initialized(root)
    with sqlite3.connect(root / "baseline.sqlite") as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM sqlite_master WHERE name IN ('partial', 'schema_migration')"
            ).fetchone()[0]
            == 0
        )
