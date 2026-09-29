"""Fresh-root real server/browser integration; uses installed Node + Google Chrome."""

import os
import re
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CLI = Path(sys.executable).parent / "cdt"


def main():
    with tempfile.TemporaryDirectory(prefix="cdt-smoke-") as temporary:
        root = Path(temporary) / "data"
        subprocess.run([str(CLI), "init", "--data-dir", str(root)], check=True)
        subprocess.run([str(CLI), "doctor", "--data-dir", str(root)], check=True)
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        server = subprocess.Popen(
            [str(CLI), "serve", "--data-dir", str(root), "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            if not select.select([server.stdout], [], [], 10)[0]:
                raise RuntimeError("Server did not emit its launch URL")
            line = server.stdout.readline()
            url = re.search(r"http://127\.0\.0\.1:\d+/#session=\S+", line)
            if not url:
                raise RuntimeError("Server did not produce a launch URL")
            import urllib.request

            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(50):
                try:
                    with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Server readiness timed out")
            listener = subprocess.check_output(
                ["/usr/sbin/lsof", "-nP", "-a", "-p", str(server.pid), "-iTCP", "-sTCP:LISTEN"],
                text=True,
            )
            assert f"127.0.0.1:{port} (LISTEN)" in listener and "*:" not in listener
            env = os.environ.copy()
            env["CDT_SMOKE_URL"] = url.group()
            env["CDT_SMOKE_SCREENSHOT"] = str(
                PROJECT / "docs/execution/screenshots/2026-09-27-empty-overview.png"
            )
            subprocess.run(
                ["node", "frontend/scripts/browser-smoke.mjs"],
                cwd=PROJECT,
                env=env,
                check=True,
                timeout=60,
            )
            busy = subprocess.run([str(CLI), "init", "--data-dir", str(root)], capture_output=True)
            assert busy.returncode != 0, "Maintenance must fail while serving"
        finally:
            server.send_signal(signal.SIGINT)
            try:
                server.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.communicate()
                raise RuntimeError("Server failed graceful shutdown") from None
        assert server.returncode in (0, -signal.SIGINT), server.returncode
        subprocess.run([str(CLI), "init", "--data-dir", str(root)], check=True)
        print(
            "Server smoke passed: fresh init, doctor, loopback listener, maintenance exclusion, graceful shutdown, repeat init."
        )


if __name__ == "__main__":
    main()
