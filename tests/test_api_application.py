"""HTTP contract probes use isolated synthetic stubs, never a data root or acquisition."""

import json

import pytest
from fastapi.testclient import TestClient

from chesterfield_twin.api.app import create_app
from chesterfield_twin.domain.application import (
    ActivationResult,
    BaselineRecord,
    EvidenceResponse,
    RecordPage,
    RecordQuery,
    ReleaseComparison,
    ReleaseSummary,
)
from chesterfield_twin.domain.candidates import DocumentCandidate
from chesterfield_twin.domain.contracts import Bootstrap
from chesterfield_twin.domain.releases import ReleaseEdge, ReleaseNode
from chesterfield_twin.storage import StorageBusyError, StorageError
from chesterfield_twin.storage.application import ApplicationError

ORIGIN = "http://127.0.0.1:8765"
SECRET = "L" * 43
RELEASE = "a" * 64
OTHER_RELEASE = "b" * 64
SENTINEL = "synthetic-private-secret /private/strategy.sqlite SELECT secret"


def synthetic_record():
    excerpt = "<script>synthetic evidence only</script>"
    candidate = DocumentCandidate(
        natural_key="synthetic-document:1", title="Synthetic fixture", scope_caveat="Two localities",
        excerpt=excerpt, extracted_page_sha256="c" * 64,
        locator=dict(pdf_page=1, printed_page="1", heading="Synthetic", text_start=0,
                     text_end=len(excerpt)),
        provenance=dict(
            source_id="synthetic-source", artifact_sha256="d" * 64, artifact_bytes=10,
            spec_sha256="e" * 64, transform_id="synthetic-transform", synthetic=True,
            retention="Synthetic test only", retrieval=dict(
                url="https://example.org/synthetic.pdf", retrieved_at="2026-09-29T12:00:00Z",
                status_code=200, media_type="application/pdf",
            ),
        ),
    )
    return BaselineRecord(version_id=candidate.fingerprint, candidate=candidate)


class ApplicationStub:
    """Typed transport stub; it grants no storage verification or real activation evidence."""

    def __init__(self):
        self.calls = []
        self.failure = None
        self.record = synthetic_record()
        self.node = ReleaseNode(kind="candidate", key=self.record.version_id,
                                payload=self.record.candidate.model_dump(mode="json"))
        self.raw_node = ReleaseNode(kind="raw", key="d" * 64,
                                   payload={"synthetic": True})

    def called(self, method, *arguments):
        self.calls.append((method, *arguments))
        if self.failure is not None:
            raise self.failure

    def bootstrap(self):
        self.called("bootstrap")
        return Bootstrap(active_release_id=RELEASE, has_baseline=True, capabilities=[
            "release_activation", "release_reads", "release_comparison",
        ])

    def summary(self, release_id):
        self.called("summary", release_id)
        return ReleaseSummary(
            release_id=release_id, synthetic=True, candidate_report_id="c" * 64,
            build_report_id="d" * 64, counts={"document_excerpt": 1},
            coverage={"fixture": "Synthetic"}, sources=(),
        )

    def records(self, release_id, *, query=None):
        self.called("records", release_id, query)
        query = query or RecordQuery()
        return RecordPage(release_id=release_id, synthetic=True, records=(self.record,), total=1,
                          offset=query.offset, limit=query.limit)

    def evidence(self, release_id, version_id):
        self.called("evidence", release_id, version_id)
        nodes = tuple(sorted((self.node, self.raw_node), key=lambda node: node.node_id))
        return EvidenceResponse(release_id=release_id, synthetic=True, record=self.record,
                                nodes=nodes, edges=(ReleaseEdge(
                                    from_node=self.node.node_id, role="raw",
                                    to_node=self.raw_node.node_id,
                                ),))

    def compare(self, old_release_id, new_release_id):
        self.called("compare", old_release_id, new_release_id)
        return ReleaseComparison(old_release_id=old_release_id, new_release_id=new_release_id,
                                 old_synthetic=True, new_synthetic=True,
                                 unchanged_count=1, changes=())

    def activate(self, release_id):
        self.called("activate", release_id)
        raise ApplicationError("synthetic_release")


def authenticated_client(service=None, **kwargs):
    app = create_app(bootstrap=Bootstrap, launch_secret=SECRET, application=service, **kwargs)
    client = TestClient(app, base_url=ORIGIN, raise_server_exceptions=False)
    session = client.post("/api/v1/session", json={"secret": SECRET}, headers={"Origin": ORIGIN})
    assert session.status_code == 200
    return client, session.json()["csrf_token"]


def activation_headers(csrf):
    return {"Origin": ORIGIN, "X-CSRF-Token": csrf}


def test_reads_echo_explicit_pins_synthetic_flags_and_typed_filters():
    service = ApplicationStub()
    client, _ = authenticated_client(service)
    # Bootstrap is the only pointer discovery read; every later request supplies its own pin.
    assert client.get("/api/v1/bootstrap").json()["active_release_id"] == RELEASE
    summary = client.get(f"/api/v1/releases/{OTHER_RELEASE}")
    assert summary.status_code == 200
    assert summary.json()["release_id"] == OTHER_RELEASE
    assert "active_release_id" not in summary.json()
    records = client.get("/api/v1/records", params={
        "release_id": OTHER_RELEASE, "kind": "observation", "geography_id": "51041000100",
        "metric_code": "poverty_rate", "offset": 3, "limit": 2,
    })
    assert records.status_code == 200
    assert service.calls[-1] == ("records", OTHER_RELEASE, RecordQuery(
        kind="observation", geography_id="51041000100", metric_code="poverty_rate",
        offset=3, limit=2,
    ))
    evidence = client.get(f"/api/v1/evidence/{service.record.version_id}",
                          params={"release_id": OTHER_RELEASE})
    assert evidence.status_code == 200
    assert service.calls[-1] == ("evidence", OTHER_RELEASE, service.record.version_id)
    assert evidence.json()["record"]["candidate"]["excerpt"].startswith("<script>")
    assert evidence.headers["content-type"] == "application/json"
    nodes = evidence.json()["nodes"]
    node_ids = {node["node_id"] for node in nodes}
    assert node_ids == {service.node.node_id, service.raw_node.node_id}
    for node in nodes:
        original = ReleaseNode.model_validate({key: node[key] for key in ("kind", "key", "payload")})
        assert node["node_id"] == original.node_id
    for edge in evidence.json()["edges"]:
        assert edge["from_node"] in node_ids and edge["to_node"] in node_ids
    changes = client.get("/api/v1/changes", params={
        "old_release_id": OTHER_RELEASE, "new_release_id": RELEASE,
    })
    assert changes.status_code == 200
    assert service.calls[-1] == ("compare", OTHER_RELEASE, RELEASE)
    assert changes.json()["old_release_id"] == OTHER_RELEASE
    assert changes.json()["new_release_id"] == RELEASE
    assert changes.json()["old_synthetic"] and changes.json()["new_synthetic"]
    for response in (summary, records, evidence):
        assert response.json()["release_id"] == OTHER_RELEASE
        assert response.json()["synthetic"] is True
        assert response.json()["current_dependencies_verified"] is True
        assert response.headers["cache-control"] == "no-store"
    assert records.json()["records"][0]["candidate"]["provenance"]["synthetic"] is True
    assert all(call[0] != "activate" for call in service.calls)


def test_bounded_defaults_and_boundary_values_reach_service():
    service = ApplicationStub()
    client, _ = authenticated_client(service)
    assert client.get("/api/v1/records", params={"release_id": RELEASE}).status_code == 200
    assert service.calls[-1] == ("records", RELEASE, RecordQuery())
    for offset, limit in ((0, 1), (303, 303)):
        result = client.get("/api/v1/records", params={
            "release_id": RELEASE, "offset": offset, "limit": limit,
        })
        assert result.status_code == 200
        assert service.calls[-1][-1] == RecordQuery(offset=offset, limit=limit)


@pytest.mark.parametrize("path", [
    "/api/v1/records", "/api/v1/evidence/" + "c" * 64, "/api/v1/changes",
    f"/api/v1/changes?old_release_id={RELEASE}",
    f"/api/v1/changes?new_release_id={RELEASE}",
    "/api/v1/releases/not-a-release",
    f"/api/v1/records?release_id={'A' * 64}",
    f"/api/v1/records?release_id={'a' * 63}",
    f"/api/v1/evidence/not-a-version?release_id={RELEASE}",
    f"/api/v1/changes?old_release_id=latest&new_release_id={RELEASE}",
])
def test_required_valid_explicit_pins_fail_before_storage(path):
    service = ApplicationStub()
    client, _ = authenticated_client(service)
    assert client.get(path).status_code == 422
    assert service.calls == []


@pytest.mark.parametrize("key,value", [
    ("kind", "all"), ("kind", "document"), ("geography_id", "51570000100"),
    ("metric_code", "sql"), ("offset", "-1"), ("offset", "304"), ("offset", "1.5"),
    ("offset", "true"), ("limit", "0"), ("limit", "304"), ("limit", "none"),
])
def test_filters_and_pagination_are_allowlisted(key, value):
    service = ApplicationStub()
    client, _ = authenticated_client(service)
    assert client.get("/api/v1/records", params={"release_id": RELEASE, key: value}).status_code == 422
    assert service.calls == []


@pytest.mark.parametrize("path", [
    f"/api/v1/releases/{RELEASE}?release_id={RELEASE}",
    f"/api/v1/records?release_id={RELEASE}&release_id={RELEASE}",
    f"/api/v1/records?release_id={RELEASE}&release_id={OTHER_RELEASE}",
    f"/api/v1/records?release_id={RELEASE}&limit=1&limit=2",
    f"/api/v1/records?release_id={RELEASE}&kind=boundary&kind=observation",
    f"/api/v1/records?release_id={RELEASE}&query=SELECT",
    f"/api/v1/evidence/{'c' * 64}?release_id={RELEASE}&release_id={RELEASE}",
    f"/api/v1/evidence/{'c' * 64}?release_id={RELEASE}&path=private",
    f"/api/v1/changes?old_release_id={RELEASE}&new_release_id={OTHER_RELEASE}&latest=true",
    f"/api/v1/changes?old_release_id={RELEASE}&old_release_id={RELEASE}&new_release_id={RELEASE}",
    f"/api/v1/changes?old_release_id={RELEASE}&new_release_id={RELEASE}&new_release_id={RELEASE}",
])
def test_duplicate_and_unknown_query_keys_reject_before_storage(path):
    service = ApplicationStub()
    client, _ = authenticated_client(service)
    response = client.get(path)
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_query"}
    assert service.calls == []


@pytest.mark.parametrize("method,path", [
    ("GET", f"/api/v1/releases/{RELEASE}"),
    ("GET", f"/api/v1/records?release_id={RELEASE}"),
    ("GET", f"/api/v1/evidence/{'c' * 64}?release_id={RELEASE}"),
    ("GET", f"/api/v1/changes?old_release_id={RELEASE}&new_release_id={OTHER_RELEASE}"),
    ("POST", f"/api/v1/releases/{RELEASE}/activate"),
])
def test_routes_exist_without_service_and_fail_safely(method, path):
    client, csrf = authenticated_client()
    result = client.request(method, path, headers=activation_headers(csrf))
    assert result.status_code == 503
    assert result.json() == {"detail": "application_unavailable"}
    assert result.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("failure,status,code", [
    (ApplicationError("invalid_query"), 422, "invalid_query"),
    (ApplicationError("unknown_release"), 404, "unknown_release"),
    (ApplicationError("unknown_evidence"), 404, "unknown_evidence"),
    (ApplicationError("synthetic_release"), 409, "synthetic_release"),
    (ApplicationError("release_unavailable"), 409, "release_unavailable"),
    (StorageBusyError(SENTINEL), 503, "storage_busy"),
    (StorageError(SENTINEL), 503, "storage_unavailable"),
    (RuntimeError(SENTINEL), 500, "Local operation failed; run cdt doctor"),
])
def test_errors_are_fixed_and_sanitized_for_reads_bootstrap_and_activation(failure, status, code):
    service = ApplicationStub()
    service.failure = failure
    # Even underlying/chained exception text cannot become an HTTP error.
    failure.__cause__ = RuntimeError(SENTINEL)
    client, csrf = authenticated_client(service)
    for method, path in (
        ("GET", "/api/v1/bootstrap"),
        ("GET", f"/api/v1/releases/{RELEASE}"),
        ("GET", f"/api/v1/records?release_id={RELEASE}"),
        ("GET", f"/api/v1/evidence/{'c' * 64}?release_id={RELEASE}"),
        ("GET", f"/api/v1/changes?old_release_id={RELEASE}&new_release_id={OTHER_RELEASE}"),
        ("POST", f"/api/v1/releases/{RELEASE}/activate"),
    ):
        result = client.request(method, path, headers=activation_headers(csrf))
        assert result.status_code == status
        assert result.json() == {"detail": code}
        assert SENTINEL not in result.text + str(result.headers)


def test_every_application_route_requires_session_and_exact_host_origin():
    service = ApplicationStub()
    app = create_app(bootstrap=Bootstrap, launch_secret=SECRET, application=service)
    client = TestClient(app, base_url=ORIGIN)
    paths = [f"/api/v1/releases/{RELEASE}", f"/api/v1/records?release_id={RELEASE}",
             f"/api/v1/evidence/{'c' * 64}?release_id={RELEASE}",
             f"/api/v1/changes?old_release_id={RELEASE}&new_release_id={RELEASE}"]
    for path in paths:
        assert client.get(path).status_code == 401
    assert client.post(f"/api/v1/releases/{RELEASE}/activate").status_code == 401
    assert service.calls == []
    client.post("/api/v1/session", json={"secret": SECRET}, headers={"Origin": ORIGIN})
    for path in paths:
        for headers, status in (({"Host": "evil.example:8765"}, 400),
                                ({"Origin": "http://localhost:8765"}, 403),
                                ({"Sec-Fetch-Site": "cross-site"}, 403)):
            assert client.get(path, headers=headers).status_code == status
    assert service.calls == []


def test_activation_requires_csrf_explicit_path_and_no_body_or_query():
    service = ApplicationStub()
    client, csrf = authenticated_client(service)
    path = f"/api/v1/releases/{RELEASE}/activate"
    for headers in ({}, {"Origin": ORIGIN}, {"X-CSRF-Token": csrf},
                    {"Origin": ORIGIN, "X-CSRF-Token": "wrong"}):
        assert client.post(path, headers=headers).status_code == 403
    assert client.post(path + "?release_id=" + OTHER_RELEASE,
                       headers=activation_headers(csrf)).status_code == 422
    assert client.post(path, json={"release_id": OTHER_RELEASE, "secret": SENTINEL},
                       headers=activation_headers(csrf)).json() == {"detail": "invalid_query"}
    assert client.post(path, content=b"{}", headers=activation_headers(csrf)).status_code == 422
    assert client.post("/api/v1/releases/latest/activate",
                       headers=activation_headers(csrf)).status_code == 422
    assert service.calls == []
    result = client.post(path, headers=activation_headers(csrf))
    assert result.status_code == 409
    assert result.json() == {"detail": "synthetic_release"}
    assert service.calls == [("activate", RELEASE)]


def test_activation_echoes_committed_result_from_isolated_service_stub():
    service = ApplicationStub()
    result = ActivationResult(release_id=OTHER_RELEASE, active_release_id=OTHER_RELEASE,
                              previous_release_id=RELEASE, changed=True, synthetic=False)

    def activation_stub(release_id):
        service.called("activate", release_id)
        return result

    service.activate = activation_stub
    client, csrf = authenticated_client(service)
    response = client.post(f"/api/v1/releases/{OTHER_RELEASE}/activate",
                           headers=activation_headers(csrf))
    assert response.status_code == 200
    assert response.json() == result.model_dump(mode="json")
    assert service.calls == [("activate", OTHER_RELEASE)]


def test_factory_schema_and_lifespan_do_no_implicit_work_and_bootstrap_is_checked(tmp_path):
    service = ApplicationStub()
    assets = tmp_path / "ui"
    assets.mkdir()
    (assets / "index.html").write_text("<html>Synthetic UI assets</html>")

    def unchecked_bootstrap():
        pytest.fail("Unchecked bootstrap used despite application service")

    app = create_app(bootstrap=unchecked_bootstrap, application=service,
                     launch_secret=SECRET, frontend_dir=assets)
    schema = app.openapi()
    assert service.calls == []
    assert SENTINEL not in json.dumps(schema)
    assert "requestBody" not in schema["paths"]["/api/v1/releases/{release_id}/activate"]["post"]
    assert schema["paths"]["/api/v1/records"]["get"]["parameters"][0]["required"] is True
    with TestClient(app, base_url=ORIGIN) as client:
        assert service.calls == []
        assert client.get("/").status_code == 200
        assert client.get(f"/api/v1/releases/{RELEASE}").status_code == 401
        client.post("/api/v1/session", json={"secret": SECRET}, headers={"Origin": ORIGIN})
        bootstrap = client.get("/api/v1/bootstrap")
        assert bootstrap.json()["capabilities"] == [
            "release_activation", "release_reads", "release_comparison",
        ]
        assert client.get(f"/api/v1/releases/{RELEASE}").status_code == 200
    assert service.calls == [("bootstrap",), ("summary", RELEASE)]
    assert create_app(bootstrap=Bootstrap).openapi() == schema
