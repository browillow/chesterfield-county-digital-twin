"""Bounded, atomic normalization of the audited NAD83 tract archive."""

import io
import math
import re
import stat
import struct
import zipfile
import zlib
from pathlib import PurePosixPath

import shapefile

from chesterfield_twin.domain.candidates import (
    BoundaryCandidate,
    BoundaryLocator,
    CandidateBatch,
    Geometry,
    Retrieval,
    digest,
)
from chesterfield_twin.sources.common import SourceValidationError, failure, prepare

SOURCE_ID = "census_cartographic_2023_va_tract_500k"
MAX_BYTES = 8 * 1024 * 1024
MAX_UNCOMPRESSED = 32 * 1024 * 1024
MAX_FILES = 32
REQUIRED_FIELDS = {"STATEFP", "COUNTYFP", "TRACTCE", "GEOIDFQ", "GEOID", "NAME",
                   "NAMELSAD", "ALAND", "AWATER"}


def reject(code, message):
    raise SourceValidationError(code, message)


def _contains(point, ring):
    x, y = point
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return inside


def _geometry(shape):
    if shape.shapeType != shapefile.POLYGON:
        reject("geometry", "Only two-dimensional polygon shapes are accepted")
    starts = list(shape.parts)
    if not starts or starts[0] != 0 or starts != sorted(set(starts)):
        reject("geometry", "Invalid polygon part offsets")
    rings = []
    for start, end in zip(starts, starts[1:] + [len(shape.points)], strict=True):
        ring = [[float(x), float(y)] for x, y in shape.points[start:end]]
        if (len(ring) < 4 or ring[0] != ring[-1]
                or len({tuple(p) for p in ring[:-1]}) < 3
                or any(not math.isfinite(x) or not math.isfinite(y)
                       or not -180 <= x <= 180 or not -90 <= y <= 90 for x, y in ring)):
            reject("geometry", "Polygon rings must be finite, closed geographic coordinates")
        area = shapefile.signed_area(ring)
        if not math.isfinite(area) or area == 0:
            reject("geometry", "Degenerate polygon ring")
        rings.append((ring, area))
    # Shapefile exterior rings are clockwise. Retain rings without repair.
    # Containment grouping is not a full self-intersection/crossing topology test.
    polygons = [[ring] for ring, area in rings if area < 0]
    if not polygons:
        reject("geometry", "Polygon has no clockwise exterior ring")
    for ring, area in rings:
        if area > 0:
            containing = [p for p in polygons if any(_contains(point, p[0]) for point in ring[:-1])]
            if not containing:
                reject("geometry", "Interior ring has ambiguous or absent exterior")
            min(containing, key=lambda p: abs(shapefile.signed_area(p[0]))).append(ring)
    return Geometry(type="Polygon" if len(polygons) == 1 else "MultiPolygon",
                    coordinates=polygons[0] if len(polygons) == 1 else polygons)


def normalize_boundaries(raw: bytes, retrieval: Retrieval, spec_bytes: bytes, *,
                         synthetic: bool) -> CandidateBatch:
    """Preserve source coordinates and square-metre attributes; never create display CRS."""
    try:
        spec, provenance = prepare(
            raw, retrieval, spec_bytes, source_id=SOURCE_ID, transform_id="boundaries/1",
            synthetic=synthetic, media_types={"application/zip", "application/x-zip-compressed",
                                             "application/octet-stream"}, max_bytes=MAX_BYTES)
        expected = {"boundary_vintage": "2023", "geography_definition": "2020 Census tracts",
                    "state_fips": "51", "county_fips_filter": "041", "join_field": "GEOID",
                    "crs": "NAD83 geographic coordinates"}
        if any(spec.get(k) != v for k, v in expected.items()):
            reject("spec_geography", "Specification geography, vintage or CRS is incompatible")
        if set(spec.get("required_fields", [])) != REQUIRED_FIELDS:
            reject("spec_schema", "Specification must require the audited boundary fields")
        counts = (spec.get("expected_state_records"), spec.get("expected_county_records"))
        if (any(type(n) is not int or n <= 0 for n in counts)
                or counts[1] > counts[0] or (not synthetic and counts != (2186, 75))):
            reject("spec_count", "Invalid expected source cardinality")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_UNCOMPRESSED:
                reject("archive_limit", "Archive exceeds member or expanded byte limits")
            names = [m.filename for m in members]
            if len(names) != len(set(names)):
                reject("archive_path", "Duplicate ZIP member names")
            for m in members:
                path = PurePosixPath(m.filename)
                if (not m.filename or "\\" in m.filename or path.is_absolute()
                        or ".." in path.parts or ":" in m.filename
                        or stat.S_ISLNK(m.external_attr >> 16) or m.flag_bits & 1):
                    reject("archive_path", "Unsafe or encrypted ZIP member")
            shp_names = [n for n in names if n.endswith(".shp")]
            if len(shp_names) != 1:
                reject("archive_schema", "Expected exactly one Shapefile")
            shp_name = shp_names[0]
            stem = shp_name[:-4]
            if any(stem + ext not in names for ext in (".shx", ".dbf", ".prj")):
                reject("archive_schema", "Missing required Shapefile component")
            wkt = archive.read(stem + ".prj").decode("ascii").strip()
            compact = re.sub(r"\s+", "", wkt).upper()
            if (not compact.startswith('GEOGCS["GCS_NORTH_AMERICAN_1983",')
                    or 'DATUM["D_NORTH_AMERICAN_1983",' not in compact
                    or 'SPHEROID["GRS_1980",6378137,298.257222101]' not in compact
                    or 'PRIMEM["GREENWICH",0]' not in compact
                    or not re.search(r'UNIT\["DEGREE",0\.017453292519943(?:3|295)\]', compact)
                    or "PROJCS[" in compact):
                reject("crs", "Expected audited NAD83 geographic degree CRS")
            with shapefile.Reader(shp=io.BytesIO(archive.read(shp_name)),
                                  shx=io.BytesIO(archive.read(stem + ".shx")),
                                  dbf=io.BytesIO(archive.read(stem + ".dbf"))) as reader:
                fields = {f[0]: f for f in reader.fields[1:]}
                if (not REQUIRED_FIELDS <= fields.keys() or len(reader) != counts[0]
                        or reader.numShapes != counts[0]):
                    reject("schema", "Shapefile schema or statewide record count differs")
                if (any(fields[k][1:3] != ["C", n] for k, n in
                        (("STATEFP", 2), ("COUNTYFP", 3), ("TRACTCE", 6), ("GEOID", 11)))
                        or any(fields[k][1] != "N" or fields[k][3] != 0
                               for k in ("ALAND", "AWATER"))):
                    reject("schema", "Geography or area field types differ")
                candidates, seen = [], set()
                for index, item in enumerate(reader.iterShapeRecords()):
                    row = item.record.as_dict()
                    geoid = row["GEOID"]
                    if (not re.fullmatch(r"51[0-9]{9}", geoid)
                            or geoid != row["STATEFP"] + row["COUNTYFP"] + row["TRACTCE"]
                            or row["GEOIDFQ"] != "1400000US" + geoid or geoid in seen):
                        reject("geography", "Duplicate or inconsistent Virginia tract geography")
                    seen.add(geoid)
                    geometry = _geometry(item.shape)
                    if any(type(row[k]) is not int or row[k] < 0 for k in ("ALAND", "AWATER")):
                        reject("area", "Source areas must be nonnegative integer square metres")
                    if row["COUNTYFP"] == "041":
                        candidates.append(BoundaryCandidate(
                            natural_key=f"{SOURCE_ID}/{geoid}/2023", provenance=provenance,
                            geography_id=geoid, name=row["NAMELSAD"], crs_wkt=wkt,
                            geometry=geometry, geometry_sha256=digest(geometry.model_dump(mode="json")),
                            land_area_m2=row["ALAND"], water_area_m2=row["AWATER"],
                            locator=BoundaryLocator(archive_member=stem + ".dbf", record=index,
                                                    geography_id=geoid),
                            limitations=spec["limitations"]))
                if len(seen) != counts[0] or len(candidates) != counts[1]:
                    reject("cardinality", "Normalized source or county cardinality differs")
                return CandidateBatch(candidates=candidates)
    except SourceValidationError as exc:
        return failure(exc.code, str(exc))
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OSError,
            zipfile.BadZipFile, shapefile.ShapefileException, struct.error, EOFError, zlib.error) as exc:
        return failure("malformed_boundary", f"Boundary archive cannot be normalized ({type(exc).__name__})")
