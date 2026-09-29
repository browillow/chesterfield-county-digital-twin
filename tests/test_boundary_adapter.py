"""Generated synthetic archives; no downloaded source bytes are test fixtures."""

import io
import struct
import zipfile
from pathlib import Path

import pytest
import shapefile

from chesterfield_twin.domain.candidates import Retrieval
from chesterfield_twin.sources import boundaries

SPEC = Path('source_specs/census_2023_va_tract_boundaries.toml').read_bytes()
WKT = ('GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",'
       'SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],'
       'UNIT["Degree",0.017453292519943295]]')
RING = [[-78, 37], [-78, 38], [-77, 38], [-77, 37], [-78, 37]]


def fixture(*, records=1, geoid='51041000100', ring=None, wkt=WKT, extra=None, area=20):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON) as writer:
        for name, width in [('STATEFP', 2), ('COUNTYFP', 3), ('TRACTCE', 6),
                            ('GEOIDFQ', 20), ('GEOID', 11), ('NAME', 20), ('NAMELSAD', 30)]:
            writer.field(name, 'C', width)
        writer.field('ALAND', 'N', 14, 0)
        writer.field('AWATER', 'N', 14, 0)
        for _ in range(records):
            writer.poly([list(ring) if ring is not None else RING])
            writer.record('51', '041', '000100', '1400000US' + geoid, geoid,
                          '1', 'Census Tract 1', area, 0)
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w') as archive:
        for suffix, data in [('shp', shp.getvalue()), ('shx', shx.getvalue()),
                             ('dbf', dbf.getvalue()), ('prj', wkt.encode())]:
            if suffix == 'shp' and ring is not None and ring[0] != ring[-1]:
                data = data[:-16] + struct.pack('<2d', *ring[-1])
            archive.writestr('synthetic.' + suffix, data)
        if extra:
            archive.writestr(extra, b'fixture')
    spec = SPEC.replace(b'expected_state_records = 2186',
                        f'expected_state_records = {records}'.encode())
    spec = spec.replace(b'expected_county_records = 75',
                        f'expected_county_records = {records}'.encode())
    return result.getvalue(), spec


def normalize(raw, spec, **kwargs):
    retrieval = Retrieval(url='https://www2.census.gov/geo/tiger/GENZ2023/shp/'
                          'cb_2023_51_tract_500k.zip', retrieved_at='2026-09-29T12:00:00Z',
                          status_code=200, media_type='application/zip')
    return boundaries.normalize_boundaries(raw, retrieval, spec, synthetic=kwargs.get('synthetic', True))


def test_repeat_and_change_identity():
    raw, spec = fixture()
    first = normalize(raw, spec).candidates[0]
    repeat = normalize(raw, spec).candidates[0]
    changed = normalize(*fixture(area=21)).candidates[0]
    assert first.fingerprint == repeat.fingerprint
    assert first.fingerprint != changed.fingerprint
    assert first.natural_key == changed.natural_key
    assert first.crs == 'EPSG:4269'
    assert first.land_area_m2 == 20
    assert first.locator.archive_member == 'synthetic.dbf'
    assert first.locator.record == 0
    assert first.provenance.synthetic


@pytest.mark.parametrize('kwargs,code', [
    ({'records': 2}, 'geography'),
    ({'geoid': '51041000101'}, 'geography'),
    ({'wkt': WKT.replace('Degree', 'Metre')}, 'crs'),
    ({'extra': '../unsafe'}, 'archive_path'),
    ({'extra': '/unsafe'}, 'archive_path'),
    ({'ring': [[-181, 37], [-181, 38], [-77, 38], [-77, 37], [-181, 37]]}, 'geometry'),
    ({'ring': [[-78, 37], [-78, 38], [-77, 38], [-77, 37], [-78, 36]]}, 'geometry'),
    ({'area': -1}, 'area'),
])
def test_atomic_failures(kwargs, code):
    batch = normalize(*fixture(**kwargs))
    assert not batch.valid and not batch.candidates
    assert batch.issues[0].code == code


def test_bad_zip_and_source_pin():
    assert not normalize(b'bad zip', fixture()[1]).valid
    batch = normalize(*fixture(), synthetic=False)
    assert batch.issues[0].code == 'artifact_pin'


def test_size_limits(monkeypatch):
    raw, spec = fixture()
    monkeypatch.setattr(boundaries, 'MAX_BYTES', len(raw) - 1)
    assert normalize(raw, spec).issues[0].code == 'byte_limit'
    monkeypatch.setattr(boundaries, 'MAX_BYTES', len(raw))
    monkeypatch.setattr(boundaries, 'MAX_UNCOMPRESSED', 10)
    assert normalize(raw, spec).issues[0].code == 'archive_limit'
    monkeypatch.setattr(boundaries, 'MAX_UNCOMPRESSED', 10000)
    monkeypatch.setattr(boundaries, 'MAX_FILES', 3)
    assert normalize(raw, spec).issues[0].code == 'archive_limit'


def test_rings_and_orphan_hole():
    shape = shapefile.Shape(shapefile.POLYGON)
    shape.parts = [0, 5]
    hole = [[-77.8, 37.2], [-77.2, 37.2], [-77.2, 37.8], [-77.8, 37.8], [-77.8, 37.2]]
    shape.points = RING + hole
    assert len(boundaries._geometry(shape).coordinates) == 2
    shape.points = RING + [[x + 10, y] for x, y in hole]
    with pytest.raises(boundaries.SourceValidationError, match='absent exterior'):
        boundaries._geometry(shape)
    shape.parts = [0]
    shape.points = [[float('nan'), 37]] + RING[1:]
    with pytest.raises(boundaries.SourceValidationError):
        boundaries._geometry(shape)


def test_missing_component_and_truncated_binary():
    raw, spec = fixture()
    for missing in ('synthetic.shx', None):
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(raw)) as original, zipfile.ZipFile(output, 'w') as changed:
            for name in original.namelist():
                if name == missing:
                    continue
                data = original.read(name)
                changed.writestr(name, data[:12] if missing is None and name.endswith('.shp') else data)
        batch = normalize(output.getvalue(), spec)
        assert not batch.valid and not batch.candidates
