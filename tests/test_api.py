import secrets

import pytest
from fastapi.testclient import TestClient

from chesterfield_twin.api.app import create_app
from chesterfield_twin.domain.contracts import Bootstrap

ORIGIN = "http://127.0.0.1:8765"


def client_and_secret(tmp_path=None):
    secret = secrets.token_urlsafe(32)
    assets = None
    if tmp_path:
        assets = tmp_path / "ui"
        assets.mkdir()
        (assets / "index.html").write_text("<html><body>Local assets only</body></html>")
    app = create_app(bootstrap=Bootstrap, launch_secret=secret, frontend_dir=assets)
    return TestClient(app, base_url=ORIGIN), secret


def exchange(client, secret):
    return client.post("/api/v1/session", json={"secret": secret}, headers={"Origin": ORIGIN})


def test_session_required_single_use_and_restart():
    client, secret = client_and_secret()
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/api/v1/bootstrap").status_code == 401
    result = exchange(client, secret)
    assert result.status_code == 200
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=strict" in result.headers["set-cookie"]
    assert exchange(client, secret).status_code == 401
    assert client.get("/api/v1/bootstrap").json() == Bootstrap().model_dump()
    restarted, _ = client_and_secret()
    restarted.cookies.update(client.cookies)
    assert restarted.get("/api/v1/bootstrap").status_code == 401


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.example:8765"},
        {"Origin": "https://evil.example"},
        {"Origin": "http://127.0.0.1:1234"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_rebinding_and_cross_origin_rejected(headers):
    client, _ = client_and_secret()
    assert client.get("/healthz", headers=headers).status_code in {400, 403}


def test_exchange_requires_origin_and_bounded_redacted_body():
    client, secret = client_and_secret()
    assert client.post("/api/v1/session", json={"secret": secret}).status_code == 403
    result = exchange(client, "invalid-secret-input")
    assert result.status_code == 422
    assert "invalid-secret-input" not in result.text
    assert exchange(client, "x" * 1000).status_code == 413
    assert exchange(client, "x" * 43).status_code == 401
    assert exchange(client, secret).status_code == 200


def test_mutations_require_csrf_even_with_session():
    client, secret = client_and_secret()
    csrf = exchange(client, secret).json()["csrf_token"]
    assert client.post("/api/v1/not-implemented").status_code == 403
    assert client.post("/api/v1/not-implemented", headers={"Origin": ORIGIN}).status_code == 403
    assert (
        client.post(
            "/api/v1/not-implemented", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}
        ).status_code
        == 404
    )


def test_static_files_and_no_documentation_or_path_traversal(tmp_path):
    client, _ = client_and_secret(tmp_path)
    result = client.get("/")
    assert result.status_code == 200
    assert "Local assets only" in result.text
    assert "frame-ancestors 'none'" in result.headers["content-security-policy"]
    for path in ("/docs", "/openapi.json", "/..%2f..%2fpyproject.toml", "/private/strategy.sqlite"):
        assert client.get(path).status_code == 404


def test_failure_does_not_disclose_paths_or_private_values():
    def fail():
        raise RuntimeError("private-sentinel /Users/private/path")

    secret = secrets.token_urlsafe(32)
    client = TestClient(
        create_app(bootstrap=fail, launch_secret=secret),
        base_url=ORIGIN,
        raise_server_exceptions=False,
    )
    exchange(client, secret)
    result = client.get("/api/v1/bootstrap")
    assert result.status_code == 500
    assert "private-sentinel" not in result.text


def test_streamed_oversize_and_unicode_secret_fail_cleanly():
    client, _ = client_and_secret()
    result = client.post(
        "/api/v1/session",
        content=iter([b"x" * 300, b"x" * 300]),
        headers={"Origin": ORIGIN, "Content-Type": "application/json"},
    )
    assert result.status_code == 413
    assert exchange(client, "é" * 43).status_code == 401


def test_checked_in_openapi_matches_runtime():
    import json

    from chesterfield_twin.config import PROJECT_ROOT

    expected = json.loads((PROJECT_ROOT / "openapi.json").read_text())
    assert create_app(bootstrap=Bootstrap).openapi() == expected
