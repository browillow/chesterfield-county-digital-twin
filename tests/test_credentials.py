import getpass
import pickle
import subprocess
import warnings
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from chesterfield_twin import credentials as c

SENTINEL = "distinctive-test-secret-927"


def test_provider_redaction_clear_and_serialization():
    provider = c.CensusCredentialProvider(SecretStr(SENTINEL))
    assert provider.get_census_api_key().get_secret_value() == SENTINEL
    assert SENTINEL not in repr(provider) + str(provider)
    with pytest.raises(TypeError, match="cannot be serialized"):
        pickle.dumps(provider)
    provider.clear()
    provider.clear()
    assert provider.get_census_api_key() is None
    with pytest.raises(c.CredentialError) as error:
        c.CensusCredentialProvider(SENTINEL)
    assert SENTINEL not in str(error.value)


@pytest.mark.parametrize("source", ["none", "unknown", "prompt", "keychain"])
def test_unselected_environment_discarded(monkeypatch, source):
    monkeypatch.setenv(c._ENV_NAME, SENTINEL)
    monkeypatch.setattr(c.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(c.sys, "platform", "linux")
    if source == "none":
        assert c.load_census_credentials(source).get_census_api_key() is None
    else:
        with pytest.raises(c.CredentialError) as error:
            c.load_census_credentials(source)
        assert SENTINEL not in str(error.value)
    assert c._ENV_NAME not in c.os.environ


@pytest.mark.parametrize("value", ["", "a b", "\t", "é", "\x7f", "a" * 257, "key\n"])
def test_environment_invalid_sanitized(monkeypatch, value):
    monkeypatch.setenv(c._ENV_NAME, value)
    with pytest.raises(c.CredentialError, match="^Invalid Census credential$") as error:
        c.load_census_credentials("env")
    assert error.value.__cause__ is None
    assert c._ENV_NAME not in c.os.environ


def test_environment_explicit_and_missing(monkeypatch):
    monkeypatch.setenv(c._ENV_NAME, SENTINEL)
    assert c.load_census_credentials("env").get_census_api_key().get_secret_value() == SENTINEL
    with pytest.raises(c.CredentialError):
        c.load_census_credentials("env")


@pytest.mark.parametrize("value", ["!", "a" * 256])
def test_credential_length_boundaries(monkeypatch, value):
    monkeypatch.setenv(c._ENV_NAME, value)
    assert c.load_census_credentials("env").get_census_api_key().get_secret_value() == value


def test_terminal_backend_error_sanitized(monkeypatch):
    def fail():
        raise OSError(SENTINEL)
    monkeypatch.setattr(c.sys, "stdin", SimpleNamespace(isatty=fail))
    with pytest.raises(c.CredentialError, match="prompt failed") as error:
        c.load_census_credentials("prompt")
    assert SENTINEL not in str(error.value)


@pytest.mark.parametrize("failure", [EOFError(SENTINEL), KeyboardInterrupt(), RuntimeError(SENTINEL)])
def test_prompt_failures(monkeypatch, failure):
    monkeypatch.setattr(c.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    def fail(*args):
        raise failure
    monkeypatch.setattr(c.getpass, "getpass", fail)
    with pytest.raises(c.CredentialError, match="^Census credential prompt failed$") as error:
        c.load_census_credentials("prompt")
    assert SENTINEL not in str(error.value)
    assert error.value.__cause__ is None


def test_prompt_success_and_no_echo_fallback(monkeypatch):
    monkeypatch.setattr(c.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(c.getpass, "getpass", lambda _: SENTINEL)
    assert c.load_census_credentials("prompt").get_census_api_key().get_secret_value() == SENTINEL
    def unsafe(*args):
        warnings.warn(SENTINEL, getpass.GetPassWarning)
        pytest.fail("warning must abort before echoed fallback")
    monkeypatch.setattr(c.getpass, "getpass", unsafe)
    with pytest.raises(c.CredentialError, match="prompt failed"):
        c.load_census_credentials("prompt")


def test_keychain_fixed_read_only_command(monkeypatch):
    monkeypatch.setattr(c.sys, "platform", "darwin")
    monkeypatch.setenv(c._ENV_NAME, "unselected-secret")
    def run(argv, **kwargs):
        assert argv == ["/usr/bin/security", "find-generic-password", "-s",
                        "ChesterfieldTwin", "-a", "census_api_key", "-w"]
        assert kwargs == dict(shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=5, check=False,
                              env=dict(c.os.environ))
        assert c._ENV_NAME not in kwargs["env"]
        return SimpleNamespace(returncode=0, stdout=(SENTINEL + "\n").encode(), stderr=b"")
    monkeypatch.setattr(c.subprocess, "run", run)
    assert c.load_census_credentials("keychain").get_census_api_key().get_secret_value() == SENTINEL


@pytest.mark.parametrize("outcome", ["failed", "timeout", "oserror", "nonascii", "two_newlines"])
def test_keychain_errors_sanitized_no_fallback(monkeypatch, outcome):
    monkeypatch.setattr(c.sys, "platform", "darwin")
    monkeypatch.setenv(c._ENV_NAME, SENTINEL)
    def run(*args, **kwargs):
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(SENTINEL, 5, output=SENTINEL, stderr=SENTINEL)
        if outcome == "oserror":
            raise OSError(SENTINEL)
        return SimpleNamespace(returncode=1 if outcome == "failed" else 0,
                               stdout=b"\xff" if outcome == "nonascii" else
                               (SENTINEL + "\n\n").encode(), stderr=SENTINEL.encode())
    monkeypatch.setattr(c.subprocess, "run", run)
    with pytest.raises(c.CredentialError) as error:
        c.load_census_credentials("keychain")
    assert SENTINEL not in str(error.value)
    assert error.value.__cause__ is None
    assert c._ENV_NAME not in c.os.environ
