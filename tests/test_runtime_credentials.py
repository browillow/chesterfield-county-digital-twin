"""Credential startup integration uses synthetic sentinels, never local secrets."""

import json
import os
import sys
import threading

import pytest

from chesterfield_twin import cli
from chesterfield_twin.credentials import load_census_credentials
from chesterfield_twin.storage import initialize

SENTINEL = "synthetic-census-secret-DO-NOT-DISCLOSE"


def test_serve_injects_before_browser_and_clears_without_persistence(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    initialize(root)
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    monkeypatch.setenv("CDT_CENSUS_API_KEY", SENTINEL)
    monkeypatch.setattr(sys, "argv", ["cdt", "serve", "--data-dir", str(root),
                                    "--census-key-source", "env", "--open"])
    seen = {}
    browser_started = threading.Event()

    def browser(url, port, stopped):
        seen["browser_env"] = os.environ.get("CDT_CENSUS_API_KEY")
        seen["url"] = url
        browser_started.set()

    def server(app, **kwargs):
        assert browser_started.wait(2)
        provider = app.state.census_credentials
        assert provider.get_census_api_key().get_secret_value() == SENTINEL
        assert "CDT_CENSUS_API_KEY" not in os.environ
        seen["provider"] = provider
        seen["schema"] = json.dumps(app.openapi())

    monkeypatch.setattr(cli, "open_when_ready", browser)
    monkeypatch.setattr(cli.uvicorn, "run", server)
    assert cli.main() == 0
    assert seen["browser_env"] is None
    assert seen["provider"].get_census_api_key() is None
    assert SENTINEL not in seen["url"] + seen["schema"] + str(capsys.readouterr())
    after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("failure", ["factory", "server", "interrupt"])
def test_startup_failure_clears_credentials(tmp_path, monkeypatch, capsys, failure):
    root = tmp_path / "data"
    initialize(root)
    monkeypatch.setenv("CDT_CENSUS_API_KEY", SENTINEL)
    provider = load_census_credentials("env")
    monkeypatch.setattr(cli, "load_census_credentials", lambda source: provider)
    monkeypatch.setattr(sys, "argv", ["cdt", "serve", "--data-dir", str(root),
                                    "--census-key-source", "env"])

    def fail(*args, **kwargs):
        if failure == "interrupt":
            raise KeyboardInterrupt
        raise RuntimeError(SENTINEL)

    if failure == "factory":
        monkeypatch.setattr(cli, "create_app", fail)
    else:
        monkeypatch.setattr(cli.uvicorn, "run", fail)
    if failure == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            cli.main()
    else:
        assert cli.main() == 1
    assert provider.get_census_api_key() is None
    assert SENTINEL not in str(capsys.readouterr())


def test_missing_explicit_env_fails_before_app_or_browser(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    initialize(root)
    monkeypatch.delenv("CDT_CENSUS_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["cdt", "serve", "--data-dir", str(root),
                                    "--census-key-source", "env", "--open"])
    monkeypatch.setattr(cli, "create_app", lambda **kw: pytest.fail("app started"))
    assert cli.main() == 1
    assert "credential unavailable or invalid" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["init", "doctor"])
def test_maintenance_does_not_acquire_credentials(tmp_path, monkeypatch, command):
    root = tmp_path / "data"
    initialize(root)
    monkeypatch.setattr(sys, "argv", ["cdt", command, "--data-dir", str(root)])
    monkeypatch.setattr(cli, "load_census_credentials", lambda source: pytest.fail("acquired key"))
    assert cli.main() == 0


@pytest.mark.parametrize("arguments", [
    ["serve", "--census-api-key", SENTINEL],
    ["serve", "--census-key-source", SENTINEL],
    ["serve", "--port", SENTINEL],
    [SENTINEL],
])
def test_argument_errors_do_not_echo_accidental_secrets(monkeypatch, capsys, arguments):
    monkeypatch.setattr(sys, "argv", ["cdt", *arguments])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert SENTINEL not in str(capsys.readouterr())
