import json
import subprocess
import sys
from pathlib import Path

import pytest

from chesterfield_twin import cli
from chesterfield_twin.config import PROJECT_ROOT, resolve_data_root


def run_cli(*arguments):
    command = Path(sys.executable).parent / "cdt"
    return subprocess.run([str(command), *arguments], capture_output=True, text=True)


def test_fresh_init_doctor_repeat_and_outside_repo(tmp_path):
    root = tmp_path / "data"
    for _ in range(2):
        assert run_cli("init", "--data-dir", str(root)).returncode == 0
    doctor = run_cli("doctor", "--data-dir", str(root))
    assert doctor.returncode == 0, doctor.stderr
    result = json.loads(doctor.stdout)
    assert result["storage"] == "compatible"
    assert result["fts5"] and result["foreign_keys"] and result["writable_storage"]
    assert not list(root.glob("*probe*"))
    rejected = run_cli("init", "--data-dir", str(PROJECT_ROOT / "data"))
    assert rejected.returncode != 0
    assert not (PROJECT_ROOT / "data").exists()


def test_resolution_precedence_and_symlink_to_checkout(tmp_path, monkeypatch):
    monkeypatch.setenv("CDT_DATA_DIR", str(tmp_path / "environment"))
    assert resolve_data_root() == tmp_path / "environment"
    assert resolve_data_root(tmp_path / "explicit") == tmp_path / "explicit"
    link = tmp_path / "link"
    link.symlink_to(PROJECT_ROOT, target_is_directory=True)
    with pytest.raises(ValueError):
        resolve_data_root(link / "data")
    with pytest.raises(ValueError):
        resolve_data_root(tmp_path / "CloudStorage" / "data")
    with pytest.raises(ValueError):
        resolve_data_root("/private/tmp")


def test_serve_only_binds_loopback_and_never_installs(tmp_path, monkeypatch, capsys):
    from chesterfield_twin.storage import initialize

    root = tmp_path / "data"
    initialize(root)
    captured = {}
    monkeypatch.setattr(sys, "argv", ["cdt", "serve", "--data-dir", str(root), "--port", "9876"])
    monkeypatch.setattr(cli.uvicorn, "run", lambda app, **kwargs: captured.update(kwargs))
    assert cli.main() == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["workers"] == 1
    assert captured["proxy_headers"] is False
    assert captured["access_log"] is False
    assert "/#session=" in capsys.readouterr().out


def test_uninitialized_fails_without_creating_databases(tmp_path):
    result = run_cli("serve", "--data-dir", str(tmp_path / "empty"))
    assert result.returncode != 0
    assert not list(tmp_path.rglob("*.sqlite"))
    assert run_cli("serve", "--host", "0.0.0.0").returncode != 0


def test_corrupt_store_produces_bounded_cli_error(tmp_path):
    root = tmp_path / "corrupt"
    assert run_cli("init", "--data-dir", str(root)).returncode == 0
    (root / "baseline.sqlite").write_bytes(b"synthetic-corrupt-database")
    result = run_cli("doctor", "--data-dir", str(root))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "failed" in result.stderr
    assert "synthetic-corrupt-database" not in result.stderr
    result = run_cli("init", "--data-dir", str(root))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
