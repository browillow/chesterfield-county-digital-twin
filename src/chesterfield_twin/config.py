"""Central resolution of the external runtime data root."""

import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_data_root(explicit: str | Path | None = None) -> Path:
    raw = explicit or os.environ.get("CDT_DATA_DIR")
    root = (
        Path(raw).expanduser().resolve()
        if raw
        else Path.home() / "Library/Application Support/ChesterfieldTwin"
    )
    root = root.resolve()
    shared_roots = {
        Path(p).resolve()
        for p in (
            "/tmp",
            "/var/tmp",
            "/private",
            "/Applications",
            "/Library",
            "/System",
            "/usr",
            "/opt",
            "/bin",
            "/sbin",
            "/Volumes",
            tempfile.gettempdir(),
        )
    }
    if root in shared_roots:
        raise ValueError("Choose a dedicated data directory, not a shared system directory")
    if root == PROJECT_ROOT or PROJECT_ROOT in root.parents or root in PROJECT_ROOT.parents:
        raise ValueError("Data root must be outside and separate from the source checkout")
    if any(
        part in {"Mobile Documents", "CloudStorage", "Dropbox", "OneDrive"} for part in root.parts
    ):
        raise ValueError("Active data must use local storage, outside cloud-sync folders")
    return root
