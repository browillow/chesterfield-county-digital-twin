"""Small, offline runtime feature checks."""

import platform
import sqlite3
import sys


def runtime_checks() -> dict:
    with sqlite3.connect(":memory:") as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE VIRTUAL TABLE feature_probe USING fts5(text)")
        foreign_keys = bool(db.execute("PRAGMA foreign_keys").fetchone()[0])
    return {
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "sqlite": sqlite3.sqlite_version,
        "fts5": True,
        "foreign_keys": foreign_keys,
        "managed_environment": sys.prefix != sys.base_prefix,
    }
