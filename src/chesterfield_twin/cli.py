"""Foreground local runtime. Installed dependencies only; no implicit downloads."""

import argparse
import json
import secrets
import shutil
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

from .api.app import create_app
from .config import PROJECT_ROOT, resolve_data_root
from .diagnostics import runtime_checks


def port_number(value):
    number = int(value)
    if not 1024 <= number <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1024 and 65535")
    return number


def open_when_ready(url, port, stopped):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(50):
        if stopped.wait(0.1):
            return
        try:
            with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=0.2) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (urllib.error.URLError, TimeoutError):
            continue


def main():
    parser = argparse.ArgumentParser(prog="cdt", description="Local Chesterfield evidence tool")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "doctor", "serve"):
        command = sub.add_parser(name)
        command.add_argument(
            "--data-dir", type=Path, help="External local runtime root (or CDT_DATA_DIR)"
        )
        if name == "serve":
            command.add_argument("--port", type=port_number, default=8765)
            command.add_argument(
                "--open", action="store_true", help="Open a one-time local session in your browser"
            )
    args = parser.parse_args()
    try:
        from .storage import BaselineRepository, check_initialized, initialize, maintenance_lock

        root = resolve_data_root(args.data_dir)
        if args.command == "init":
            initialize(root)
            print("Local baseline and private stores initialized.")
        elif args.command == "doctor":
            result = runtime_checks()
            with maintenance_lock(root, exclusive=False):
                check_initialized(root)
                with tempfile.TemporaryFile(dir=root) as probe:
                    probe.write(b"cdt storage probe")
                    probe.flush()
            result.update(
                writable_storage=True,
                storage="compatible",
                free_bytes=shutil.disk_usage(root).free,
                frontend_built=(PROJECT_ROOT / "frontend/dist/index.html").is_file(),
            )
            print(json.dumps(result, indent=2))
        else:
            with maintenance_lock(root, exclusive=False):
                check_initialized(root)
                repo = BaselineRepository(root)
                secret = secrets.token_urlsafe(32)
                app = create_app(
                    bootstrap=repo.bootstrap,
                    port=args.port,
                    launch_secret=secret,
                    frontend_dir=PROJECT_ROOT / "frontend/dist",
                )
                url = f"http://127.0.0.1:{args.port}/#session={secret}"
                stopped = threading.Event()
                thread = None
                if args.open:
                    thread = threading.Thread(
                        target=open_when_ready, args=(url, args.port, stopped), daemon=True
                    )
                    thread.start()
                else:
                    print(f"One-time local session URL: {url}", flush=True)
                try:
                    uvicorn.run(
                        app,
                        host="127.0.0.1",
                        port=args.port,
                        workers=1,
                        proxy_headers=False,
                        access_log=False,
                        log_level="warning",
                    )
                finally:
                    stopped.set()
                    if thread:
                        thread.join(timeout=1)
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
        # Commands never echo source/private content. Details are checked by tests,
        # while the user gets an actionable command-level failure.
        print(
            f"cdt {args.command} failed ({type(exc).__name__}). "
            "Use an external local --data-dir; run cdt init for a fresh root. "
            "If assets are missing, run npm --prefix frontend ci && npm --prefix frontend run build. "
            "Stop other processes before maintenance; preserve incompatible stores for recovery.",
            file=sys.stderr,
        )
        return 1
    return 0
