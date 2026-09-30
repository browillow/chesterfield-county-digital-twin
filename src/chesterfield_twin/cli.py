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

from .acquisition import AcquisitionError, acquire_acs, preflight_acquisition
from .api.app import create_app
from .config import PROJECT_ROOT, resolve_data_root
from .credentials import CredentialError, load_census_credentials
from .diagnostics import runtime_checks


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Unknown arguments can contain a mistakenly pasted credential.
        self.print_usage(sys.stderr)
        self.exit(2, "Invalid command arguments; use --help. Never pass credential values as arguments.\n")


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
    parser = SafeArgumentParser(prog="cdt", description="Local Chesterfield evidence tool")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)
    release = sub.add_parser("release", help="Explicit sealed build or current verification")
    release_commands = release.add_subparsers(dest="release_command", required=True)
    build = release_commands.add_parser("build", help="Build and seal without activation")
    build.add_argument("--data-dir", type=Path, required=True)
    build.add_argument("--run-id", required=True)
    build.add_argument("--import-id", action="append", required=True)
    build.add_argument("--report-id", required=True,
                       help="Explicit candidate validation report; current evidence must match")
    verify = release_commands.add_parser("verify", help="Verify current sealed dependencies")
    verify.add_argument("--data-dir", type=Path, required=True)
    verify.add_argument("--release-id", required=True)
    acquire = sub.add_parser("acquire-acs", help="Explicit bounded 2023 Subject acquisition")
    acquire.add_argument("--audit-dir", type=Path, required=True,
                         help="New external local audit directory; must not exist")
    acquire.add_argument("--boundary", type=Path, required=True,
                         help="Previously audited, unchanged 2023 Virginia tract ZIP")
    acquire.add_argument("--census-key-source", choices=("none", "prompt", "env", "keychain"),
                         default="none", help="Explicit local credential source; default: none")
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
            command.add_argument(
                "--census-key-source", choices=("none", "prompt", "env", "keychain"),
                default="none", help="Explicit local credential source; default: none",
            )
    args = parser.parse_args()
    credentials = None
    try:
        if args.command == "acquire-acs":
            preflight_acquisition(boundary_path=args.boundary, audit_dir=args.audit_dir)
            credentials = load_census_credentials(args.census_key_source)
            result = acquire_acs(credentials=credentials, boundary_path=args.boundary,
                                 audit_dir=args.audit_dir)
            print(json.dumps({"acquired": True, "sha256": result.sha256,
                              "byte_length": result.byte_length,
                              "tract_count": result.tract_count,
                              "candidate_count": result.candidate_count,
                              "staged": False, "release_activated": False}, indent=2))
            return 0

        from .storage import BaselineRepository, check_initialized, initialize, maintenance_lock

        root = resolve_data_root(args.data_dir)
        if args.command == "release":
            from .storage.releases import ReleaseBuilder

            builder = ReleaseBuilder(root, PROJECT_ROOT)
            if args.release_command == "build":
                result = builder.build(args.run_id, tuple(args.import_id),
                                       expected_report_id=args.report_id)
                print(json.dumps({
                    "sealed": result.sealed,
                    "release_id": result.manifest.release_id if result.manifest else None,
                    "build_report_id": result.report.report_id,
                    "candidate_report_id": result.report.content.candidate_report_id,
                    "synthetic": result.report.content.synthetic,
                    "issue_codes": [issue.code for issue in result.report.content.issues],
                    "active_pointer_changed": False,
                }, indent=2))
                return 0 if result.sealed else 1
            manifest = builder.read_release(args.release_id, verify_current=True)
            print(json.dumps({
                "release_id": manifest.release_id,
                "current_dependencies_verified": True,
                "synthetic": manifest.content.synthetic,
                "version_count": len(manifest.content.selection.version_ids),
                "active_pointer_changed": False,
            }, indent=2))
            return 0
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
                credentials = load_census_credentials(args.census_key_source)
                secret = secrets.token_urlsafe(32)
                app = create_app(
                    bootstrap=repo.bootstrap,
                    port=args.port,
                    launch_secret=secret,
                    frontend_dir=PROJECT_ROOT / "frontend/dist",
                    credentials=credentials,
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
    except KeyboardInterrupt:
        if args.command == "release":
            print("Release operation interrupted. Preserve the root and reports; "
                  "no activation was requested.", file=sys.stderr)
            return 130
        if args.command != "acquire-acs":
            raise
        print("ACS acquisition cancelled; preserve any audit directory. "
              "No automatic retry was made.", file=sys.stderr)
        return 130
    except AcquisitionError:
        print("ACS acquisition did not complete; preserve any audit directory. "
              "Check the pinned boundary, fresh external --audit-dir and local credential source. "
              "A changed source representation requires review; no automatic retry was made.",
              file=sys.stderr)
        return 1
    except CredentialError:
        print(
            "Local Census credential unavailable or invalid. Check the selected source; "
            "use --census-key-source prompt in an interactive terminal for hidden entry.",
            file=sys.stderr,
        )
        return 1
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
        # Commands never echo source/private content. Details are checked by tests,
        # while the user gets an actionable command-level failure.
        if args.command == "acquire-acs":
            print("ACS acquisition failed. Preserve existing evidence and use a fresh external "
                  "--audit-dir; inspect the local setup before retrying.", file=sys.stderr)
            return 1
        if args.command == "release":
            print("Release operation failed. Preserve the root and reports. Check the explicit "
                  "selection and retained dependencies; do not upgrade an earlier store. "
                  "No activation was requested.", file=sys.stderr)
            return 1
        print(
            f"cdt {args.command} failed ({type(exc).__name__}). "
            "Use an external local --data-dir; run cdt init for a fresh root. "
            "If assets are missing, run npm --prefix frontend ci && npm --prefix frontend run build. "
            "Stop other processes before maintenance; preserve incompatible stores for recovery.",
            file=sys.stderr,
        )
        return 1
    finally:
        if credentials is not None:
            credentials.clear()
    return 0
