"""Offline acquisition fixtures do not establish publisher access."""
import json
from urllib.parse import urlencode

import pytest
from pydantic import SecretStr
from test_acs_adapter import fixture

from chesterfield_twin import acquisition as a
from chesterfield_twin.credentials import CensusCredentialProvider

KEY = 'synthetic-secret-XYZ'


@pytest.fixture
def setup(monkeypatch, tmp_path):
    boundary = tmp_path / 'boundary.zip'
    boundary.write_bytes(b'synthetic boundary stand-in')
    geoids = [f'51041{i:06}' for i in range(75)]
    monkeypatch.setattr(a, '_boundary', lambda path, spec: (boundary.read_bytes(), geoids))
    raw = json.dumps(fixture()).encode()
    url = a.BASE + '?' + urlencode({'get': ','.join(a.FIELDS), 'for': 'tract:*',
                                    'in': 'state:51 county:041'})
    metadata = dict(request_url=url, final_url=url, retrieved_at='2026-09-29T12:00:00Z',
                    status_code=200, media_type='application/json', elapsed_seconds=0.1)
    calls = []
    def transport(key):
        calls.append(key)
        return metadata, raw
    monkeypatch.setattr(a, '_transport', transport)
    return boundary, tmp_path / 'audit', raw, metadata, calls


def acquire(setup):
    boundary, audit, *_ = setup
    return a.acquire_acs(credentials=CensusCredentialProvider(SecretStr(KEY)),
                         boundary_path=boundary, audit_dir=audit)


def test_roundtrip_exact_original_and_specs(setup):
    boundary, audit, raw, _, calls = setup
    result = acquire(setup)
    assert calls == [KEY]
    assert result.candidate_count == 225 and result.tract_count == 75
    assert (audit / 'response.json').read_bytes() == raw
    assert result.sha256 == a._sha(raw)
    assert {p.name for p in audit.iterdir()} == a.FILES
    value = a.read_acquisition(audit_dir=audit, boundary_path=boundary)
    assert value.raw == raw and value.spec_bytes == a._specs()[0]
    assert raw.decode() not in repr(value)
    assert KEY not in repr(result) + repr(value)
    assert all(KEY.encode() not in p.read_bytes() for p in audit.iterdir())


def test_none_no_network(setup):
    boundary, audit, _, _, calls = setup
    with pytest.raises(a.AcquisitionError, match='credential_missing'):
        a.acquire_acs(credentials=CensusCredentialProvider(), boundary_path=boundary,
                      audit_dir=audit)
    assert not calls and not audit.exists()


@pytest.mark.parametrize('field,value', [('synthetic', True), ('accepted', False),
    ('schema_version', True), ('byte_length', True), ('tract_count', True),
    ('candidate_count', 224), ('status_code', True), ('elapsed_seconds', True),
    ('elapsed_seconds', float('inf')), ('media_type', 'text/html'),
    ('sha256', '0' * 64), ('geoid_sha256', '0' * 64), ('request_url', a.BASE)])
def test_readback_manifest_tamper(setup, field, value):
    boundary, audit, *_ = setup
    acquire(setup)
    path = audit / 'manifest.json'
    manifest = json.loads(path.read_bytes())
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(a.AcquisitionError):
        a.read_acquisition(audit_dir=audit, boundary_path=boundary)


@pytest.mark.parametrize('change', ['raw', 'spec', 'boundary', 'extra', 'path'])
def test_readback_bundle_tamper(setup, change):
    boundary, audit, *_ = setup
    acquire(setup)
    if change == 'raw':
        (audit / 'response.json').write_bytes(b'[]')
    elif change == 'spec':
        (audit / 'acs_spec.toml').write_bytes(b'bad')
    elif change == 'boundary':
        boundary.write_bytes(b'changed')
    elif change == 'extra':
        (audit / 'extra').touch()
    else:
        path = audit / 'response.json'
        path.unlink()
        path.symlink_to(boundary)
    with pytest.raises(a.AcquisitionError):
        a.read_acquisition(audit_dir=audit, boundary_path=boundary)


def test_geoid_set_and_unknown_annotation_rejected(setup, monkeypatch):
    _, audit, _, metadata, _ = setup
    for mutation in ('geoid', 'annotation', 'limit'):
        rows = fixture()
        if mutation == 'geoid':
            rows[-1][-1] = '999999'
        elif mutation == 'annotation':
            rows[1][6] = 'unknown'
        raw = json.dumps(rows).encode()
        if mutation == 'limit':
            raw += b' ' * 1_000_000
        monkeypatch.setattr(a, '_transport', lambda key: (metadata, raw))
        with pytest.raises(a.AcquisitionError, match='source_validation'):
            acquire(setup)
        assert not audit.exists()


@pytest.mark.parametrize('raw', [KEY.encode(), KEY.replace('-', '%2D').encode(),
    json.dumps([KEY]).encode(), ('["' + ''.join('\\u%04x' % ord(c) for c in KEY) + '"]').encode()])
def test_credential_echo_before_disk(setup, monkeypatch, raw):
    _, audit, _, metadata, _ = setup
    monkeypatch.setattr(a, '_transport', lambda key: (metadata, raw))
    with pytest.raises(a.AcquisitionError, match='credential_echo') as error:
        acquire(setup)
    assert KEY not in str(error.value) and error.value.__cause__ is None
    assert not audit.exists() and not list(audit.parent.glob('.acs-*'))


def test_fresh_external_destination_and_no_side_effects(setup):
    boundary, audit, _, _, calls = setup
    a.preflight_acquisition(boundary_path=boundary, audit_dir=audit)
    assert not audit.exists() and not calls
    for path in (a.PROJECT_ROOT / 'forbidden-audit', boundary, audit.parent):
        with pytest.raises(a.AcquisitionError):
            a.preflight_acquisition(boundary_path=boundary, audit_dir=path)
    link = audit.parent / 'link'
    link.symlink_to(audit.parent, target_is_directory=True)
    with pytest.raises(a.AcquisitionError):
        a.preflight_acquisition(boundary_path=boundary, audit_dir=link / 'audit')


def test_actual_invalid_boundary_precedes_provider_and_transfer(tmp_path):
    boundary = tmp_path / 'invalid.zip'
    boundary.write_bytes(b'not an audited archive')
    class Provider:
        def get_census_api_key(self):
            pytest.fail('provider must not be accessed')
    with pytest.raises(a.AcquisitionError, match='boundary'):
        a.acquire_acs(credentials=Provider(), boundary_path=boundary, audit_dir=tmp_path / 'audit')


def test_atomic_publication_collision(tmp_path):
    source, target = tmp_path / 'source', tmp_path / 'target'
    source.mkdir()
    target.mkdir()
    with pytest.raises(a.AcquisitionError, match='publication'):
        a._publish(source, target)
    assert source.is_dir() and target.is_dir()


def test_retained_metadata_echo_rejected(setup, monkeypatch):
    _, audit, raw, metadata, _ = setup
    metadata = dict(metadata, media_type='application/json; marker=' + KEY)
    monkeypatch.setattr(a, '_transport', lambda key: (metadata, raw))
    with pytest.raises(a.AcquisitionError, match='credential_echo'):
        acquire(setup)
    assert not audit.exists()


def test_final_spec_and_manifest_scan_precedes_disk(setup):
    boundary, audit, *_ = setup
    # A deliberately short synthetic key collides only with the retained spec.
    with pytest.raises(a.AcquisitionError, match='credential_echo'):
        a.acquire_acs(credentials=CensusCredentialProvider(SecretStr('publisher')),
                      boundary_path=boundary, audit_dir=audit)
    assert not audit.exists() and not list(audit.parent.glob('.acs-*'))
