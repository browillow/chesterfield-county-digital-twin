"""Local persistence with strict baseline/private and release boundaries."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import secrets
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

from chesterfield_twin.domain.contracts import Bootstrap, Measurement

_BUSY_TIMEOUT_MS = 5_000
_DATABASES = {
    "baseline.sqlite": "baseline",
    "private/strategy.sqlite": "private",
}


class StorageError(RuntimeError):
    """Base error for an unsafe or incompatible storage state."""


class StorageBusyError(StorageError):
    """The maintenance lock is held by another process."""


class MigrationError(StorageError):
    """The on-disk schema is unknown or differs from this application."""


def _assert_not_symlink(path: Path) -> None:
    if path.is_symlink():
        raise StorageError(f"managed path must not be a symlink: {path}")


def _managed_path(root: Path, relative: str | Path) -> Path:
    """Return a lexical child path after rejecting symlinks in every component."""
    root = Path(root)
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise StorageError("managed path must remain beneath its data root")
    _assert_not_symlink(root)
    current = root
    for part in relative.parts:
        current = current / part
        _assert_not_symlink(current)
    return current


def _secure_directory(root: Path, relative: str | Path = ".") -> Path:
    path = _managed_path(root, relative)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    _managed_path(root, relative)
    path.chmod(0o700)
    return path


def _sync_directory(path: Path) -> None:
    """Persist directory entries before committing references to newly linked objects."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _layout(root: Path) -> None:
    _assert_not_symlink(root)
    for relative in (
        ".",
        "private",
        "private/artifacts",
        "objects",
        "objects/sha256",
        "releases",
        "staging",
        "cache",
        "logs",
        "locks",
    ):
        _secure_directory(root, relative)


def _migration_files(database: str) -> list[Path]:
    directory = Path(__file__).with_name("migrations") / database
    files = sorted(directory.glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        raise MigrationError(f"no migrations packaged for {database}")
    return files


def _mutable_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=_BUSY_TIMEOUT_MS / 1000)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    return connection


def _readonly_connection(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(path))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    connection.row_factory = sqlite3.Row
    return connection


@contextlib.contextmanager
def maintenance_lock(root: Path, *, exclusive: bool) -> Iterator[None]:
    """Acquire the process-wide storage lock without waiting."""
    root = Path(root)
    _secure_directory(root, "locks")
    lock_path = _managed_path(root, "locks/maintenance.lock")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    os.fchmod(descriptor, 0o600)
    try:
        operation = (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB
        try:
            fcntl.flock(descriptor, operation)
        except BlockingIOError as exc:
            raise StorageBusyError("storage is in use") from exc
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _expected_migrations(database: str) -> list[tuple[str, str, str]]:
    expected = []
    for path in _migration_files(database):
        sql = path.read_text(encoding="utf-8")
        expected.append((path.name, hashlib.sha256(sql.encode()).hexdigest(), sql))
    return expected


def _verify_ledger(connection: sqlite3.Connection, database: str) -> None:
    try:
        actual = connection.execute(
            "SELECT migration_id, checksum FROM schema_migration ORDER BY migration_id"
        ).fetchall()
    except sqlite3.Error as exc:
        raise MigrationError(f"{database} migration ledger is missing") from exc
    expected = [(name, checksum) for name, checksum, _ in _expected_migrations(database)]
    if [tuple(row) for row in actual] != expected:
        raise MigrationError(f"{database} migration ledger is unknown or has changed")


def _initialize_database(path: Path, database: str) -> None:
    _assert_not_symlink(path)
    existed = path.exists()
    connection = _mutable_connection(path)
    path.chmod(0o600)
    try:
        if existed:
            _verify_ledger(connection, database)
            return
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "CREATE TABLE schema_migration "
                "(migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL)"
            )
            for name, checksum, sql in _expected_migrations(database):
                statement = ""
                for line in sql.splitlines(keepends=True):
                    statement += line
                    if sqlite3.complete_statement(statement):
                        connection.execute(statement)
                        statement = ""
                if statement.strip():
                    raise MigrationError(f"incomplete SQL in migration {name}")
                connection.execute(
                    "INSERT INTO schema_migration(migration_id, checksum) VALUES (?, ?)",
                    (name, checksum),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    finally:
        connection.close()
    path.chmod(0o600)


def initialize(root: Path) -> None:
    """Create a new storage pair or verify an existing compatible pair."""
    root = Path(root)
    _layout(root)
    with maintenance_lock(root, exclusive=True):
        paths = [
            (_managed_path(root, relative), database) for relative, database in _DATABASES.items()
        ]
        present = [path.exists() for path, _ in paths]
        if any(present) and not all(present):
            raise MigrationError("baseline and private databases must form a complete pair")
        for path, database in paths:
            _initialize_database(path, database)


def check_initialized(root: Path) -> None:
    """Read-only verification of both migration ledgers and database integrity."""
    root = Path(root)
    for relative, database in _DATABASES.items():
        path = _managed_path(root, relative)
        if not path.is_file():
            raise MigrationError(f"{database} database is not initialized")
        with contextlib.closing(_readonly_connection(path)) as connection:
            _verify_ledger(connection, database)
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise StorageError(f"{database} database failed integrity check")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise StorageError(f"{database} database failed foreign-key check")


class ArtifactStore:
    """Immutable public object bytes addressed by SHA-256."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def put(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        directory = _secure_directory(self.root, f"objects/sha256/{digest[:2]}")
        target = _managed_path(self.root, f"objects/sha256/{digest[:2]}/{digest}")
        if target.exists():
            if target.read_bytes() != content:
                raise StorageError("existing content address has different bytes")
            for path in (directory, directory.parent, directory.parent.parent, self.root):
                _sync_directory(path)
            return digest
        temporary = directory / f".{digest}.{os.getpid()}.{secrets.token_hex(6)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, target)
            target.chmod(0o600)
        except FileExistsError:
            if target.read_bytes() != content:
                raise StorageError("existing content address has different bytes")
        finally:
            temporary.unlink(missing_ok=True)
        # Persist the object link and new prefix directories before SQLite can reference it.
        for path in (directory, directory.parent, directory.parent.parent, self.root):
            _sync_directory(path)
        return digest

    def read(self, digest: str) -> bytes:
        """Read retained bytes only after re-verifying their content address."""
        content = self.path(digest).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise StorageError("artifact SHA-256 mismatch")
        return content

    def path(self, digest: str) -> Path:
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise StorageError("invalid artifact digest")
        target = _managed_path(self.root, f"objects/sha256/{digest[:2]}/{digest}")
        if not target.is_file():
            raise StorageError("artifact does not exist")
        return target


class BaselineRepository:
    """Read-only baseline operations safe for API and export consumers."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def bootstrap(self) -> Bootstrap:
        path = _managed_path(self.root, "baseline.sqlite")
        with contextlib.closing(_readonly_connection(path)) as connection:
            row = connection.execute(
                "SELECT active_release_id FROM app_state WHERE singleton = 1"
            ).fetchone()
            active = row[0] if row else None
            return Bootstrap(
                active_release_id=active, has_baseline=active is not None, capabilities=[]
            )

    def export_release(self, release_id: str) -> dict:
        path = _managed_path(self.root, "baseline.sqlite")
        with contextlib.closing(_readonly_connection(path)) as connection:
            release = connection.execute(
                "SELECT release_id, manifest_json, sealed_at FROM release "
                "WHERE release_id = ? AND status = 'sealed'",
                (release_id,),
            ).fetchone()
            if release is None:
                raise StorageError("release is unknown or not sealed")
            versions = connection.execute(
                "SELECT v.version_id, v.kind, v.payload_json, v.synthetic "
                "FROM release_version rv JOIN version v ON v.version_id = rv.version_id "
                "WHERE rv.release_id = ? ORDER BY v.version_id",
                (release_id,),
            ).fetchall()
            return {
                "release_id": release["release_id"],
                "sealed_at": release["sealed_at"],
                "manifest": json.loads(release["manifest_json"]),
                "versions": [
                    {
                        "version_id": row["version_id"],
                        "kind": row["kind"],
                        "payload": json.loads(row["payload_json"]),
                        "synthetic": bool(row["synthetic"]),
                    }
                    for row in versions
                ],
            }


class PrivateRepository:
    """Private persistence handle, intentionally separate from baseline access."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def add_research_item(self, item_id: str, title: str) -> None:
        path = _managed_path(self.root, "private/strategy.sqlite")
        with contextlib.closing(_mutable_connection(path)) as connection, connection:
            connection.execute(
                "INSERT INTO research_item(item_id, title) VALUES (?, ?)", (item_id, title)
            )


def insert_measurement(
    connection: sqlite3.Connection, measurement_id: str, value: Measurement
) -> None:
    """Persistence adapter used by later ingestion code and synthetic storage tests."""
    connection.execute(
        "INSERT INTO measurement "
        "(measurement_id, claim_class, value_state, value, reason, unit, universe, "
        "geography_id, geography_vintage, reference_period, synthetic) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            measurement_id,
            value.claim_class,
            value.value_state,
            value.value,
            value.reason,
            value.unit,
            value.universe,
            value.geography_id,
            value.geography_vintage,
            value.reference_period,
            value.synthetic,
        ),
    )
