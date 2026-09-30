"""Loopback-only API and per-launch browser session boundary."""

import secrets
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi import Path as PathParameter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from ..credentials import CensusCredentialProvider
from ..domain.application import (
    ActivationResult,
    CandidateKind,
    EvidenceResponse,
    MetricCode,
    RecordPage,
    RecordQuery,
    ReleaseComparison,
    ReleaseSummary,
)
from ..domain.candidates import Geoid, Sha256
from ..domain.contracts import Bootstrap, SessionRequest, SessionResponse
from ..storage import StorageBusyError, StorageError
from ..storage.application import ApplicationError, ReleaseApplication

MAX_SESSION_BODY = 512
APPLICATION_ERROR_STATUS = {
    "invalid_query": 422,
    "unknown_release": 404,
    "unknown_evidence": 404,
    "synthetic_release": 409,
    "release_unavailable": 409,
}


def create_app(
    *,
    bootstrap: Callable[[], Bootstrap],
    port: int = 8765,
    launch_secret: str | None = None,
    frontend_dir: Path | None = None,
    credentials: CensusCredentialProvider | None = None,
    application: ReleaseApplication | None = None,
) -> FastAPI:
    provider = credentials if credentials is not None else CensusCredentialProvider()
    try:
        return _create_app(
            bootstrap=bootstrap, port=port, launch_secret=launch_secret,
            frontend_dir=frontend_dir, credentials=provider, application=application,
        )
    except BaseException:
        provider.clear()
        raise


def _create_app(
    *,
    bootstrap: Callable[[], Bootstrap],
    port: int,
    launch_secret: str | None,
    frontend_dir: Path | None,
    credentials: CensusCredentialProvider,
    application: ReleaseApplication | None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            credentials.clear()

    expected_host = f"127.0.0.1:{port}"
    origin = f"http://{expected_host}"
    secret = launch_secret or secrets.token_urlsafe(32)
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    cookie_name = f"cdt_session_{port}"
    exchanged = False
    app = FastAPI(
        title="Chesterfield Twin", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None,
        lifespan=lifespan,
    )
    # Internal dependency only. Never include this provider in transport/storage models.
    app.state.census_credentials = credentials

    def selected_application(request: Request, allowed: set[str]) -> ReleaseApplication:
        keys = [key for key, _ in request.query_params.multi_items()]
        if any(key not in allowed for key in keys) or len(keys) != len(set(keys)):
            raise HTTPException(422, "invalid_query")
        if application is None:
            raise HTTPException(503, "application_unavailable")
        return application

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.headers.get("host") != expected_host:
            return JSONResponse({"detail": "Unexpected Host"}, status_code=400)
        request_origin = request.headers.get("origin")
        if request_origin is not None and request_origin != origin:
            return JSONResponse({"detail": "Cross-origin access rejected"}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site access rejected"}, status_code=403)
        if request.url.path.startswith("/api/") and request.url.path != "/api/v1/session":
            if not secrets.compare_digest(request.cookies.get(cookie_name, ""), session_token):
                return JSONResponse({"detail": "Local session required"}, status_code=401)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                if request_origin != origin or not secrets.compare_digest(
                    request.headers.get("x-csrf-token", ""), csrf_token
                ):
                    return JSONResponse({"detail": "CSRF check failed"}, status_code=403)
        try:
            response = await call_next(request)
        except Exception:
            # Do not send private context or traceback text to browser/access logs.
            response = JSONResponse(
                {"detail": "Local operation failed; run cdt doctor"}, status_code=500
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post(
        "/api/v1/session",
        response_model=SessionResponse,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": SessionRequest.model_json_schema()}},
            }
        },
    )
    async def exchange(request: Request):
        nonlocal exchanged
        if request.headers.get("origin") != origin:
            raise HTTPException(403, "Exact Origin required")
        if request.headers.get("content-type", "").split(";", 1)[0].strip() != "application/json":
            raise HTTPException(415, "JSON required")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_SESSION_BODY:
                raise HTTPException(413, "Session request too large")
            body.extend(chunk)
        try:
            candidate = SessionRequest.model_validate_json(bytes(body))
        except ValidationError:
            # Never echo submitted secrets through Pydantic's input field.
            raise HTTPException(422, "Invalid session request") from None
        if exchanged or not secrets.compare_digest(candidate.secret.encode(), secret.encode()):
            raise HTTPException(401, "Launch session expired or invalid")
        exchanged = True  # No await between validation and consumption.
        response = JSONResponse(SessionResponse(csrf_token=csrf_token).model_dump())
        response.set_cookie(
            cookie_name, session_token, httponly=True, samesite="strict", secure=False, path="/"
        )  # Loopback HTTP, per-launch token.
        return response

    @app.get("/api/v1/bootstrap", response_model=Bootstrap)
    def get_bootstrap():
        return application.bootstrap() if application is not None else bootstrap()

    @app.get("/api/v1/releases/{release_id}", response_model=ReleaseSummary)
    def get_release(request: Request, release_id: Annotated[Sha256, PathParameter()]):
        return selected_application(request, set()).summary(release_id)

    @app.get("/api/v1/records", response_model=RecordPage)
    def get_records(
        request: Request,
        release_id: Annotated[Sha256, Query()],
        kind: Annotated[CandidateKind | None, Query()] = None,
        geography_id: Annotated[Geoid | None, Query()] = None,
        metric_code: Annotated[MetricCode | None, Query()] = None,
        offset: Annotated[int, Query(ge=0, le=303)] = 0,
        limit: Annotated[int, Query(ge=1, le=303)] = 100,
    ):
        service = selected_application(
            request, {"release_id", "kind", "geography_id", "metric_code", "offset", "limit"}
        )
        query = RecordQuery(
            kind=kind, geography_id=geography_id, metric_code=metric_code,
            offset=offset, limit=limit,
        )
        return service.records(release_id, query=query)

    @app.get("/api/v1/evidence/{version_id}", response_model=EvidenceResponse)
    def get_evidence(
        request: Request,
        version_id: Annotated[Sha256, PathParameter()],
        release_id: Annotated[Sha256, Query()],
    ):
        return selected_application(request, {"release_id"}).evidence(release_id, version_id)

    @app.get("/api/v1/changes", response_model=ReleaseComparison)
    def get_changes(
        request: Request,
        old_release_id: Annotated[Sha256, Query()],
        new_release_id: Annotated[Sha256, Query()],
    ):
        return selected_application(request, {"old_release_id", "new_release_id"}).compare(
            old_release_id, new_release_id
        )

    @app.post("/api/v1/releases/{release_id}/activate", response_model=ActivationResult)
    async def activate_release(request: Request, release_id: Annotated[Sha256, PathParameter()]):
        service = selected_application(request, set())
        async for chunk in request.stream():
            if chunk:
                raise HTTPException(422, "invalid_query")
        return await run_in_threadpool(service.activate, release_id)

    @app.exception_handler(ApplicationError)
    async def application_error(request: Request, exc: ApplicationError):
        code = exc.code if exc.code in APPLICATION_ERROR_STATUS else "storage_unavailable"
        return JSONResponse({"detail": code}, status_code=APPLICATION_ERROR_STATUS.get(code, 503))

    @app.exception_handler(StorageBusyError)
    async def storage_busy(request: Request, exc: StorageBusyError):
        return JSONResponse({"detail": "storage_busy"}, status_code=503)

    @app.exception_handler(StorageError)
    async def storage_unavailable(request: Request, exc: StorageError):
        return JSONResponse({"detail": "storage_unavailable"}, status_code=503)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return JSONResponse({"detail": "Local operation failed; run cdt doctor"}, status_code=500)

    if frontend_dir is not None:
        if not (frontend_dir / "index.html").is_file():
            raise ValueError(
                "UI assets missing; run npm --prefix frontend ci && npm --prefix frontend run build"
            )
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="ui")
    return app
