"""Offline command/lifecycle checks with synthetic sentinel credentials only."""

import json
import sys
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from chesterfield_twin import cli
from chesterfield_twin.credentials import CensusCredentialProvider
from chesterfield_twin.storage import initialize

SENTINEL = "synthetic-acquisition-secret-DO-NOT-DISCLOSE"


def arguments(monkeypatch, tmp_path, *extra):
    monkeypatch.setattr(sys, "argv", ["cdt", "acquire-acs", "--audit-dir",
                                    str(tmp_path / "audit"), "--boundary",
                                    str(tmp_path / "boundary.zip"), *extra])


def test_preflight_then_explicit_credentials_then_acquisition(tmp_path, monkeypatch, capsys):
    arguments(monkeypatch, tmp_path, "--census-key-source", "prompt")
    calls = []
    provider = CensusCredentialProvider(SecretStr(SENTINEL))

    def preflight(**kwargs):
        assert kwargs == {"audit_dir": tmp_path / "audit",
                          "boundary_path": tmp_path / "boundary.zip"}
        calls.append("preflight")

    def load(source):
        assert source == "prompt"
        calls.append("credentials")
        return provider

    def acquire(**kwargs):
        assert kwargs["credentials"] is provider
        assert provider.get_census_api_key().get_secret_value() == SENTINEL
        calls.append("acquire")
        return SimpleNamespace(sha256="a" * 64, byte_length=123, tract_count=75,
                               candidate_count=225)

    monkeypatch.setattr(cli, "preflight_acquisition", preflight)
    monkeypatch.setattr(cli, "load_census_credentials", load)
    monkeypatch.setattr(cli, "acquire_acs", acquire)
    assert cli.main() == 0
    assert calls == ["preflight", "credentials", "acquire"]
    assert provider.get_census_api_key() is None
    output = capsys.readouterr()
    assert SENTINEL not in str(output)
    assert json.loads(output.out) == {"acquired": True, "sha256": "a" * 64,
                                    "byte_length": 123, "tract_count": 75,
                                    "candidate_count": 225, "staged": False,
                                    "release_activated": False}
    assert not list(tmp_path.rglob("*.sqlite"))


def test_default_none_is_explicit_and_cleared(tmp_path, monkeypatch, capsys):
    arguments(monkeypatch, tmp_path)
    provider = CensusCredentialProvider()
    monkeypatch.setattr(cli, "preflight_acquisition", lambda **kw: None)

    def load(source):
        assert source == "none"
        return provider

    def acquire(**kwargs):
        assert kwargs["credentials"].get_census_api_key() is None
        raise ValueError(SENTINEL)

    monkeypatch.setattr(cli, "load_census_credentials", load)
    monkeypatch.setattr(cli, "acquire_acs", acquire)
    assert cli.main() == 1
    assert SENTINEL not in str(capsys.readouterr())


def test_bad_preflight_never_prompts_or_fetches(tmp_path, monkeypatch, capsys):
    arguments(monkeypatch, tmp_path, "--census-key-source", "prompt")

    def fail(**kwargs):
        raise ValueError(SENTINEL)

    monkeypatch.setattr(cli, "preflight_acquisition", fail)
    monkeypatch.setattr(cli, "load_census_credentials", lambda *a: pytest.fail("key accessed"))
    monkeypatch.setattr(cli, "acquire_acs", lambda **kw: pytest.fail("network attempted"))
    assert cli.main() == 1
    assert SENTINEL not in str(capsys.readouterr())


@pytest.mark.parametrize("failure", [OSError, RuntimeError, KeyboardInterrupt])
def test_cleanup_and_safe_output_on_transfer_failure(tmp_path, monkeypatch, capsys, failure):
    arguments(monkeypatch, tmp_path, "--census-key-source", "env")
    provider = CensusCredentialProvider(SecretStr(SENTINEL))
    monkeypatch.setattr(cli, "preflight_acquisition", lambda **kw: None)
    monkeypatch.setattr(cli, "load_census_credentials", lambda *a: provider)

    def fail(**kwargs):
        raise failure(SENTINEL)

    monkeypatch.setattr(cli, "acquire_acs", fail)
    assert cli.main() == (130 if failure is KeyboardInterrupt else 1)
    assert provider.get_census_api_key() is None
    assert SENTINEL not in str(capsys.readouterr())


@pytest.mark.parametrize("command", ["init", "doctor", "serve"])
def test_existing_commands_never_acquire(tmp_path, monkeypatch, capsys, command):
    root = tmp_path / "data"
    initialize(root)
    monkeypatch.setattr(sys, "argv", ["cdt", command, "--data-dir", str(root)])
    monkeypatch.setattr(cli, "preflight_acquisition", lambda **kw: pytest.fail("preflight"))
    monkeypatch.setattr(cli, "acquire_acs", lambda **kw: pytest.fail("fetch"))
    monkeypatch.setattr(cli.uvicorn, "run", lambda *a, **kw: None)
    assert cli.main() == 0


@pytest.mark.parametrize("extra", [["--key", SENTINEL], ["--census-key-source", SENTINEL],
                                  ["--url", SENTINEL], ["--max-bytes", "99999999"]])
def test_unapproved_surface_rejected_without_echo(tmp_path, monkeypatch, capsys, extra):
    arguments(monkeypatch, tmp_path, *extra)
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 2
    assert SENTINEL not in str(capsys.readouterr())
