"""Explicit, process-local Census credentials; never persisted by this provider."""

import getpass
import os
import subprocess
import sys
import warnings

from pydantic import SecretStr

_ENV_NAME = "CDT_CENSUS_API_KEY"


class CredentialError(Exception):
    """Sanitized credential selection or loading failure."""


class CensusCredentialProvider:
    __slots__ = ("__key",)

    def __init__(self, key: SecretStr | None = None):
        if key is not None and not isinstance(key, SecretStr):
            raise CredentialError("Invalid Census credential") from None
        self.__key = None if key is None else _validated(key.get_secret_value())

    def get_census_api_key(self) -> SecretStr | None:
        return self.__key

    def clear(self) -> None:
        self.__key = None

    def __repr__(self) -> str:
        return "CensusCredentialProvider(<redacted>)"

    __str__ = __repr__

    def __reduce_ex__(self, protocol):
        raise TypeError("Credential providers cannot be serialized") from None


def _validated(value: str | None) -> SecretStr:
    if (not isinstance(value, str) or not 1 <= len(value) <= 256
            or any(not 33 <= ord(c) <= 126 for c in value)):
        raise CredentialError("Invalid Census credential") from None
    return SecretStr(value)


def load_census_credentials(source: str) -> CensusCredentialProvider:
    # Remove even an unselected development key before any backend can spawn a process.
    environment_key = os.environ.pop(_ENV_NAME, None)
    if source == "none":
        return CensusCredentialProvider()
    if source == "env":
        return CensusCredentialProvider(_validated(environment_key))
    if source == "prompt":
        try:
            terminal = sys.stdin.isatty()
        except Exception:
            raise CredentialError("Census credential prompt failed") from None
        if not terminal:
            raise CredentialError("Census credential prompt requires a terminal") from None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                value = getpass.getpass("Census API key: ")
        except (Exception, KeyboardInterrupt):
            raise CredentialError("Census credential prompt failed") from None
        return CensusCredentialProvider(_validated(value))
    if source == "keychain":
        if sys.platform != "darwin":
            raise CredentialError("Census Keychain credentials require macOS") from None
        try:
            result = subprocess.run(
                ["/usr/bin/security", "find-generic-password", "-s", "ChesterfieldTwin",
                 "-a", "census_api_key", "-w"],
                shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=5, check=False, env=dict(os.environ),
            )
            if result.returncode != 0:
                raise ValueError()
            value = result.stdout.decode("ascii")
        except (Exception, KeyboardInterrupt):
            raise CredentialError("Census Keychain credential could not be loaded") from None
        if value.endswith("\n"):
            value = value[:-1]
        return CensusCredentialProvider(_validated(value))
    raise CredentialError("Unsupported Census credential source") from None
