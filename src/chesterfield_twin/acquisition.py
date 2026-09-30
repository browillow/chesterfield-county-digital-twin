"""Explicit acquisition and verified local readback; no database authority."""
import ctypes
import hashlib
import json
import math
import os
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from chesterfield_twin._acs_transfer import BASE, FIELDS, LIMIT, echoed
from chesterfield_twin.config import PROJECT_ROOT, resolve_data_root
from chesterfield_twin.credentials import CensusCredentialProvider
from chesterfield_twin.domain.candidates import Retrieval, digest
from chesterfield_twin.sources.acs import normalize_acs
from chesterfield_twin.sources.boundaries import MAX_BYTES, normalize_boundaries

DEADLINE = 60.0
SPEC_DIR = PROJECT_ROOT / 'source_specs'
FILES = {'response.json', 'manifest.json', 'acs_spec.toml', 'boundary_spec.toml'}
KEYS = {'schema_version', 'kind', 'synthetic', 'accepted', 'request_url', 'final_url',
        'retrieved_at', 'status_code', 'media_type', 'elapsed_seconds', 'byte_length', 'sha256',
        'acs_spec_sha256', 'boundary_sha256', 'boundary_spec_sha256', 'geoid_sha256',
        'tract_count', 'candidate_count'}


class AcquisitionError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__('ACS acquisition failed: ' + code)


@dataclass(frozen=True)
class AcquisitionResult:
    audit_dir: Path
    manifest_path: Path
    raw_path: Path
    sha256: str
    byte_length: int
    tract_count: int
    candidate_count: int


@dataclass(frozen=True)
class AcquiredInput:
    raw: bytes = field(repr=False)
    retrieval: Retrieval
    spec_bytes: bytes = field(repr=False)
    manifest: dict


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read(path, limit):
    if path.is_symlink() or not path.is_file():
        raise AcquisitionError('input')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise AcquisitionError('input')
    return raw


def _specs():
    return ((SPEC_DIR / 'acs_2023_5yr_subject.toml').read_bytes(),
            (SPEC_DIR / 'census_2023_va_tract_boundaries.toml').read_bytes())


def _boundary(path, spec):
    raw = _read(path, MAX_BYTES)
    declaration = tomllib.loads(spec.decode())
    retrieval = Retrieval(url=declaration['artifact_url'], retrieved_at=declaration['retrieved_at'],
                          status_code=200, media_type='application/zip')
    batch = normalize_boundaries(raw, retrieval, spec, synthetic=False)
    geoids = sorted({c.geography_id for c in batch.candidates})
    if not batch.valid or len(geoids) != 75:
        raise AcquisitionError('boundary')
    return raw, geoids


def _destination(path):
    path = path.expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise AcquisitionError('destination')
    resolved = resolve_data_root(path)
    if resolved.exists() or not resolved.parent.is_dir():
        raise AcquisitionError('destination')
    return resolved


def preflight_acquisition(*, boundary_path: Path, audit_dir: Path) -> None:
    try:
        _destination(audit_dir)
        _, spec = _specs()
        _boundary(boundary_path, spec)
    except AcquisitionError:
        raise
    except Exception:
        raise AcquisitionError('preflight') from None


def _transport(key):
    started = time.monotonic()
    # An allowlist prevents proxy, credential, Python debugging, and TLS key-log inheritance.
    env = {k: v for k, v in os.environ.items() if k in {'SYSTEMROOT', 'WINDIR'}}
    process = None
    try:
        process = subprocess.Popen([sys.executable, '-I', str(Path(__file__).with_name(
            '_acs_transfer.py'))], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, env=env)
        process.stdin.write(key.encode('ascii'))
        process.stdin.close()
        chunks, size = [], 0
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = DEADLINE - (time.monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError('timeout')
                if not selector.select(remaining):
                    raise AcquisitionError('timeout')
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > LIMIT + 8193:
                    raise AcquisitionError('transfer')
                chunks.append(chunk)
        remaining = DEADLINE - (time.monotonic() - started)
        if remaining <= 0:
            raise AcquisitionError('timeout')
        if process.wait(timeout=remaining) != 0:
            raise AcquisitionError('transfer')
        payload = b''.join(chunks)
        if echoed(payload, key):
            raise AcquisitionError('credential_echo')
        header, raw = payload.split(b'\n', 1)
        if len(header) > 8192 or len(raw) > LIMIT:
            raise AcquisitionError('transfer')
        metadata = json.loads(header)
        metadata['elapsed_seconds'] = time.monotonic() - started
        if metadata['elapsed_seconds'] > DEADLINE:
            raise AcquisitionError('timeout')
        return metadata, raw
    except AcquisitionError:
        raise
    except Exception:
        raise AcquisitionError('transfer') from None
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            for pipe in (process.stdin, process.stdout):
                if pipe is not None:
                    pipe.close()


def _url(value):
    if not isinstance(value, str):
        raise AcquisitionError('manifest')
    parts = urlsplit(value)
    query = parse_qs(parts.query, keep_blank_values=True)
    if (parts.scheme != 'https' or parts.netloc != 'api.census.gov'
            or parts.path != urlsplit(BASE).path or parts.fragment
            or set(query) != {'get', 'for', 'in'} or query['for'] != ['tract:*']
            or query['in'] != ['state:51 county:041'] or len(query['get']) != 1
            or query['get'][0].split(',') != FIELDS):
        raise AcquisitionError('manifest')


def _validate(manifest, raw, acs_spec, boundary_spec, boundary_path):
    if not isinstance(manifest, dict) or set(manifest) != KEYS:
        raise AcquisitionError('manifest')
    fixed = {'schema_version': 1, 'kind': 'acs_subject_acquisition', 'synthetic': False,
             'accepted': True, 'status_code': 200, 'tract_count': 75, 'candidate_count': 225}
    if any(type(manifest[k]) is not type(v) or manifest[k] != v for k, v in fixed.items()):
        raise AcquisitionError('manifest')
    if (type(manifest['byte_length']) is not int or manifest['byte_length'] != len(raw)
            or type(manifest['elapsed_seconds']) not in {int, float}
            or not math.isfinite(manifest['elapsed_seconds'])
            or not 0 <= manifest['elapsed_seconds'] <= 60
            or not isinstance(manifest['retrieved_at'], str)
            or not isinstance(manifest['media_type'], str)
            or manifest['media_type'].split(';', 1)[0].strip().lower() != 'application/json'):
        raise AcquisitionError('manifest')
    _url(manifest['request_url'])
    _url(manifest['final_url'])
    if manifest['request_url'] != manifest['final_url']:
        raise AcquisitionError('manifest')
    current_acs, current_boundary = _specs()
    if acs_spec != current_acs or boundary_spec != current_boundary:
        raise AcquisitionError('specification')
    boundary, geoids = _boundary(boundary_path, boundary_spec)
    hashes = {'sha256': _sha(raw), 'acs_spec_sha256': _sha(acs_spec),
              'boundary_sha256': _sha(boundary), 'boundary_spec_sha256': _sha(boundary_spec),
              'geoid_sha256': digest(geoids)}
    if any(type(manifest[k]) is not str or manifest[k] != v for k, v in hashes.items()):
        raise AcquisitionError('integrity')
    retrieval = Retrieval(url=manifest['final_url'], retrieved_at=manifest['retrieved_at'],
                          status_code=200, media_type=manifest['media_type'])
    batch = normalize_acs(raw, retrieval, acs_spec, synthetic=False)
    if (not batch.valid or len(batch.candidates) != 225
            or sorted({c.measurement.geography_id for c in batch.candidates}) != geoids):
        raise AcquisitionError('source_validation')
    return retrieval


def _fsync_dir(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish(source, destination):
    # Atomic exclusive directory rename; never replace even an empty competing directory.
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        result = libc.renamex_np(os.fsencode(source), os.fsencode(destination), 4)
    elif sys.platform.startswith('linux'):
        result = libc.renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    else:
        raise AcquisitionError('publication_platform')
    if result != 0:
        raise AcquisitionError('publication')


def acquire_acs(*, credentials: CensusCredentialProvider, boundary_path: Path,
                audit_dir: Path) -> AcquisitionResult:
    temporary = None
    try:
        preflight_acquisition(boundary_path=boundary_path, audit_dir=audit_dir)
        secret = credentials.get_census_api_key()
        if secret is None:
            raise AcquisitionError('credential_missing')
        key = secret.get_secret_value()
        acs_spec, boundary_spec = _specs()
        boundary, geoids = _boundary(boundary_path, boundary_spec)
        metadata, raw = _transport(key)
        if echoed(raw, key) or echoed(json.dumps(metadata).encode(), key):
            raise AcquisitionError('credential_echo')
        manifest = dict(metadata, schema_version=1, kind='acs_subject_acquisition',
            synthetic=False, accepted=True, byte_length=len(raw), sha256=_sha(raw),
            acs_spec_sha256=_sha(acs_spec), boundary_sha256=_sha(boundary),
            boundary_spec_sha256=_sha(boundary_spec), geoid_sha256=digest(geoids),
            tract_count=75, candidate_count=225)
        _validate(manifest, raw, acs_spec, boundary_spec, boundary_path)
        destination = _destination(audit_dir)
        contents = {'response.json': raw, 'manifest.json': json.dumps(manifest, sort_keys=True,
                    allow_nan=False).encode(), 'acs_spec.toml': acs_spec,
                    'boundary_spec.toml': boundary_spec}
        if any(echoed(content, key) for content in contents.values()):
            raise AcquisitionError('credential_echo')
        temporary = Path(tempfile.mkdtemp(prefix='.acs-', dir=destination.parent))
        for name, content in contents.items():
            with (temporary / name).open('xb') as stream:
                os.chmod(temporary / name, 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        _fsync_dir(temporary)
        _publish(temporary, destination)
        _fsync_dir(destination.parent)
        temporary = None
        return AcquisitionResult(destination, destination / 'manifest.json',
                                 destination / 'response.json', _sha(raw), len(raw), 75, 225)
    except AcquisitionError:
        raise
    except Exception:
        raise AcquisitionError('acquisition') from None
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


def read_acquisition(*, audit_dir: Path, boundary_path: Path) -> AcquiredInput:
    try:
        root = resolve_data_root(audit_dir)
        if any(p.is_symlink() for p in (audit_dir, *audit_dir.parents)):
            raise AcquisitionError('input')
        if {p.name for p in root.iterdir()} != FILES:
            raise AcquisitionError('input')
        manifest = json.loads(_read(root / 'manifest.json', 16384))
        raw = _read(root / 'response.json', LIMIT)
        acs_spec = _read(root / 'acs_spec.toml', 65536)
        boundary_spec = _read(root / 'boundary_spec.toml', 65536)
        retrieval = _validate(manifest, raw, acs_spec, boundary_spec, boundary_path)
        return AcquiredInput(raw, retrieval, acs_spec, manifest)
    except AcquisitionError:
        raise
    except Exception:
        raise AcquisitionError('readback') from None
