"""Loopback-only API and per-launch browser session boundary."""

import secrets
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from ..domain.contracts import Bootstrap, SessionRequest, SessionResponse

MAX_SESSION_BODY = 512


def create_app(
    *,
    bootstrap: Callable[[], Bootstrap],
    port: int = 8765,
    launch_secret: str | None = None,
    frontend_dir: Path | None = None,
) -> FastAPI:
    expected_host = f"127.0.0.1:{port}"
    origin = f"http://{expected_host}"
    secret = launch_secret or secrets.token_urlsafe(32)
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    cookie_name = f"cdt_session_{port}"
    exchanged = False
    app = FastAPI(
        title="Chesterfield Twin", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None
    )

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
        return bootstrap()

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
