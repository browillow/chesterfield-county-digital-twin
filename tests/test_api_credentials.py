"""The runtime secret dependency never becomes an HTTP/storage contract."""

import json

import pytest
from fastapi.testclient import TestClient

from chesterfield_twin.api.app import create_app
from chesterfield_twin.credentials import load_census_credentials
from chesterfield_twin.domain.contracts import Bootstrap

ORIGIN = "http://127.0.0.1:8765"
SENTINEL = "synthetic-api-credential-PRIVATE"


def test_provider_lifecycle_and_http_redaction(monkeypatch):
    monkeypatch.setenv("CDT_CENSUS_API_KEY", SENTINEL)
    provider = load_census_credentials("env")
    launch_secret = "L" * 43
    failing = False

    def bootstrap():
        if failing:
            raise RuntimeError(SENTINEL)
        return Bootstrap()

    app = create_app(bootstrap=bootstrap, launch_secret=launch_secret, credentials=provider)
    with TestClient(app, base_url=ORIGIN) as client:
        assert provider.get_census_api_key().get_secret_value() == SENTINEL
        health = client.get("/healthz")
        session = client.post("/api/v1/session", json={"secret": launch_secret},
                              headers={"Origin": ORIGIN})
        baseline = client.get("/api/v1/bootstrap")
        assert baseline.json() == Bootstrap().model_dump()
        failing = True
        error = client.get("/api/v1/bootstrap")
        assert error.status_code == 500
        assert client.get("/api/v1/credentials").status_code == 404
        wire = json.dumps(app.openapi())
        for response in (health, session, baseline, error):
            wire += response.text + str(response.headers)
        for forbidden in (SENTINEL, "census_api_key", "CDT_CENSUS_API_KEY", "census-key-source"):
            assert forbidden not in wire
    assert provider.get_census_api_key() is None


def test_factory_failure_releases_supplied_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("CDT_CENSUS_API_KEY", SENTINEL)
    provider = load_census_credentials("env")
    with pytest.raises(ValueError):
        create_app(bootstrap=Bootstrap, credentials=provider, frontend_dir=tmp_path / "missing")
    assert provider.get_census_api_key() is None
