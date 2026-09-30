"""Complete generated synthetic closure fixtures, never real source evidence."""

import shutil
from pathlib import Path

import pytest
from test_validation_reports import ids, selection  # noqa: F401, F811

from chesterfield_twin.storage import ArtifactStore, StorageError
from chesterfield_twin.storage.releases import ReleaseBuilder
from chesterfield_twin.storage.validation import CandidateValidation


@pytest.fixture
def release_fixture(selection, tmp_path):  # noqa: F811
    root, staging, run, inputs, results = selection
    original = Path(__file__).resolve().parents[1]
    repository = tmp_path / 'repository'
    shutil.copytree(original, repository, ignore=shutil.ignore_patterns(
        '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.ruff_cache', 'dist'))
    # Git metadata is copied, so tracked deletions and dirty inputs remain measurable.
    builder = ReleaseBuilder(root, repository)
    selected = ids(results)
    report = CandidateValidation(root).validate(run, selected)
    return root, staging, run, selected, report, repository, builder


def test_complete_synthetic_build_readback_and_repeat(release_fixture):
    root, _, run, selected, report, _, builder = release_fixture
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues
    assert built.manifest.content.synthetic
    assert len(built.manifest.content.selection.version_ids) == 303
    assert builder.read_release(built.manifest.release_id) == built.manifest
    assert builder.build(run, tuple(reversed(selected)), expected_report_id=report.report_id) == built
    nodes = built.manifest.content.nodes
    assert sum(n.kind == 'candidate' for n in nodes) == 303
    assert {'raw', 'spec', 'retrieval', 'source', 'metric', 'document', 'transform',
            'query', 'config', 'dependency', 'code', 'schema', 'coverage'} <= {n.kind for n in nodes}
    assert 'PRIVATE-REPORT-SENTINEL' not in built.manifest.model_dump_json()
    assert ArtifactStore(root).read(built.manifest.release_id)


def test_expected_report_mismatch_and_invalid_selection(release_fixture):
    _, _, run, selected, report, _, builder = release_fixture
    failed = builder.build(run, selected, expected_report_id='0' * 64)
    assert not failed.sealed and failed.manifest is None
    failed = builder.build(run, selected[:2], expected_report_id=report.report_id)
    assert not failed.sealed
    with pytest.raises(StorageError):
        builder.build(run, selected, expected_report_id='invalid')


def test_missing_lock_rejects(release_fixture):
    _, _, run, selected, report, repository, builder = release_fixture
    (repository / 'uv.lock').unlink()
    failed = builder.build(run, selected, expected_report_id=report.report_id)
    assert not failed.sealed
    assert str(repository) not in failed.report.model_dump_json()


def test_readback_uses_retained_code_not_changed_checkout(release_fixture):
    _, _, run, selected, report, repository, builder = release_fixture
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues
    (repository / 'uv.lock').write_bytes(b'changed public checkout')
    assert builder.read_release(built.manifest.release_id) == built.manifest
    code = next(n for n in built.manifest.content.nodes if n.kind == 'code')
    retained = next(f for f in code.payload['files'] if f['path'] == 'uv.lock')
    builder.staging.objects.path(retained['sha256']).unlink()
    with pytest.raises(StorageError):
        builder.read_release(built.manifest.release_id)
    assert builder.read_release(built.manifest.release_id, verify_current=False) == built.manifest


def test_current_readback_does_not_write_objects(release_fixture, monkeypatch):
    _, _, run, selected, report, _, builder = release_fixture
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues

    def forbidden_put(data):
        raise AssertionError('readback must not mutate retained objects')

    monkeypatch.setattr(builder.staging.objects, 'put', forbidden_put)
    assert builder.read_release(built.manifest.release_id) == built.manifest


def test_repeat_build_cannot_heal_missing_sealed_dependency(release_fixture):
    _, _, run, selected, report, _, builder = release_fixture
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues
    code = next(n for n in built.manifest.content.nodes if n.kind == 'code')
    retained = next(f for f in code.payload['files'] if f['path'] == 'uv.lock')
    path = builder.staging.objects.path(retained['sha256'])
    path.unlink()
    failed = builder.build(run, selected, expected_report_id=report.report_id)
    assert not failed.sealed and not path.exists()


def test_snapshot_must_match_executing_implementation(release_fixture):
    _, _, run, selected, report, repository, builder = release_fixture
    path = repository / 'src/chesterfield_twin/sources/acs.py'
    path.write_bytes(path.read_bytes() + b'\n# changed synthetic copied implementation\n')
    failed = builder.build(run, selected, expected_report_id=report.report_id)
    assert not failed.sealed


@pytest.mark.parametrize('name,data', [('uv.lock', b'corrupt generated fixture lock'),
                                    ('frontend/package-lock.json', b'[]'),
                                    ('frontend/package-lock.json', b'null'),
                                    ('pyproject.toml', b'project = 1')])
def test_malformed_lock_rejects(release_fixture, name, data):
    _, _, run, selected, report, repository, builder = release_fixture
    (repository / name).write_bytes(data)
    failed = builder.build(run, selected, expected_report_id=report.report_id)
    assert not failed.sealed
