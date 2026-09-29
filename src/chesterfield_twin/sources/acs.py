"""Bounded normalization of the fixed 2019–2023 ACS subject-table slice."""

import json
import re
import tomllib
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlsplit

from pydantic import ValidationError

from chesterfield_twin.domain.candidates import (
    ApiLocator,
    CandidateBatch,
    ObservationCandidate,
    Retrieval,
    SourceNumber,
)
from chesterfield_twin.domain.contracts import Measurement
from chesterfield_twin.sources.common import SourceValidationError, failure, prepare

SOURCE_ID = "census_acs_2023_5yr_subject"
MAX_BYTES = 1_000_000
MAX_ROWS = 75
METRICS = {
    "median_household_income": (
        "S1901_C01_012", "Households - Median income (dollars)",
        "2023 inflation-adjusted dollars per household", "Households", "non_additive_median"),
    "poverty_rate": (
        "S1701_C03_001",
        "Percent below poverty level - Population for whom poverty status is determined",
        "percent", "Population for whom poverty status is determined",
        "published_percentage_non_additive"),
    "household_count": (
        "S1901_C01_001", "Households - Total", "households", "Households",
        "additive_only_across_mutually_exclusive_geographies_in_same_release"),
}
NONVALUES = {
    "-666666666": ("unavailable", "Insufficient sample", "-"),
    "-999999999": ("suppressed", "Insufficient cases", "N"),
    "-888888888": ("unavailable", "Not applicable or unavailable", "(X)"),
    "-222222222": ("unavailable", "Margin of error cannot be computed", "**"),
    "-333333333": ("unavailable", "Median open interval; margin of error cannot be computed", "***"),
    "-555555555": ("not_applicable", "Controlled estimate; margin of error inappropriate", "*****"),
}
ANNOTATIONS = {value[2]: value[:2] for value in NONVALUES.values()}


def reject(code, message):
    raise SourceValidationError(code, message)


def validate_spec(spec):
    fixed = {"release_id": "acs5_subject_2023", "dataset": "2023/acs/acs5/subject",
             "reference_period": "2019-2023", "publication_vintage": "2023",
             "geography": "tract", "state_fips": "51", "county_fips": "041",
             "response_media_type": "application/json"}
    if any(spec.get(key) != value for key, value in fixed.items()):
        reject("spec_slice", "Specification must describe the fixed 2023 Chesterfield slice")
    schema = spec.get("expected_schema", {})
    if schema != {"shape": "array_of_rows_with_header",
                  "identifier_fields": ["state", "county", "tract"],
                  "requested_nonmetric_fields": ["NAME"],
                  "expected_current_row_count": 75, "reject_media_types": ["text/html"]}:
        reject("spec_schema", "Unsupported ACS schema specification")
    metrics = spec.get("metrics", [])
    if not isinstance(metrics, list) or len(metrics) != len(METRICS):
        reject("spec_metrics", "Specification must contain the three selected metrics")
    seen = set()
    for metric in metrics:
        code = metric.get("code")
        if code not in METRICS or code in seen:
            reject("spec_metrics", "Unknown or repeated metric specification")
        seen.add(code)
        prefix, label, unit, universe, aggregation = METRICS[code]
        expected = {"estimate": prefix + "E", "margin_of_error": prefix + "M",
                    "estimate_annotation": prefix + "EA", "margin_of_error_annotation": prefix + "MA",
                    "label": label, "unit": unit, "universe": universe,
                    "aggregation": aggregation, "uncertainty": "published 90 percent margin of error"}
        if any(metric.get(key) != value for key, value in expected.items()):
            reject("spec_metrics", "Metric specification differs from the audited slice")
    return metrics


def source_number(raw, annotation, *, percentage, median, moe=False):
    moe_sentinels = {"-222222222", "-333333333", "-555555555"}
    moe_annotations = {"**", "***", "*****"}
    if not moe and (raw in moe_sentinels or annotation in moe_annotations):
        reject("estimate_semantics", "MOE-only non-values are not valid estimate semantics")
    if annotation is not None:
        if annotation in ANNOTATIONS:
            state, reason = ANNOTATIONS[annotation]
        elif (median and len(annotation) <= 64 and re.fullmatch(
                r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?[+-]", annotation)):
            state, reason = "unavailable", "Median is a bound rather than an exact point"
        else:
            reject("unknown_annotation", "Unrecognized ACS annotation")
        return SourceNumber(value_state=state, reason=reason, raw=raw, annotation=annotation)
    if raw is None:
        return SourceNumber(value_state="unavailable", reason="Source value is null",
                            raw=None, annotation=None)
    if raw in NONVALUES:
        state, reason, _ = NONVALUES[raw]
        return SourceNumber(value_state=state, reason=reason, raw=raw, annotation=None)
    try:
        number = Decimal(raw)
    except InvalidOperation:
        reject("numeric_value", "ACS value is not numeric")
    if not number.is_finite() or number < 0 or (percentage and number > 100):
        reject("numeric_value", "ACS value is outside the selected metric's valid range")
    return SourceNumber(value_state="observed", value=raw, raw=raw, annotation=None)


def normalize_acs(raw: bytes, retrieval: Retrieval, spec_bytes: bytes, *,
                  synthetic: bool) -> CandidateBatch:
    """Return unpublished candidates atomically; never retrieve or persist evidence."""
    try:
        spec, provenance = prepare(
            raw, retrieval, spec_bytes, source_id=SOURCE_ID, transform_id="acs-subject/1",
            synthetic=synthetic, media_types={"application/json"}, max_bytes=MAX_BYTES)
        metrics = validate_spec(spec)
        fields = {"NAME", "state", "county", "tract"}
        fields.update(metric[key] for metric in metrics for key in (
            "estimate", "margin_of_error", "estimate_annotation", "margin_of_error_annotation"))
        url = urlsplit(retrieval.url)
        if url.netloc != "api.census.gov" or url.path != "/data/2023/acs/acs5/subject":
            reject("source_url", "Retrieval URL must identify the selected Census dataset")
        query = parse_qs(url.query, keep_blank_values=True)
        if query and (set(query) != {"get", "for", "in"}
                      or query["for"] != ["tract:*"] or query["in"] != ["state:51 county:041"]
                      or len(query["get"]) != 1
                      or set(query["get"][0].split(",")) != fields - {"state", "county", "tract"}):
            reject("source_url", "Retrieval selectors differ from the selected slice")
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) != MAX_ROWS + 1:
            reject("row_count", "ACS response must contain exactly 75 tract rows and a header")
        header = rows[0]
        if (not isinstance(header, list) or any(not isinstance(x, str) for x in header)
                or len(header) != len(fields) or set(header) != fields):
            reject("schema", "ACS header must contain every exact requested field once")
        candidates, geoids = [], set()
        for row_index, row in enumerate(rows[1:], 1):
            if (not isinstance(row, list) or len(row) != len(header)
                    or any(x is not None and not isinstance(x, str) for x in row)):
                reject("schema", f"Invalid string/null row at JSON row {row_index}")
            data = dict(zip(header, row, strict=True))
            if (data["state"] != "51" or data["county"] != "041"
                    or not isinstance(data["tract"], str)
                    or not re.fullmatch(r"[0-9]{6}", data["tract"])):
                reject("geography", f"Invalid Chesterfield tract at JSON row {row_index}")
            geoid = data["state"] + data["county"] + data["tract"]
            if geoid in geoids:
                reject("duplicate_geography", f"Repeated tract at JSON row {row_index}")
            geoids.add(geoid)
            for metric in metrics:
                code = metric["code"]
                estimate = source_number(data[metric["estimate"]], data[metric["estimate_annotation"]],
                                         percentage=code == "poverty_rate",
                                         median=code == "median_household_income")
                moe = source_number(data[metric["margin_of_error"]],
                                    data[metric["margin_of_error_annotation"]],
                                    percentage=False, median=False, moe=True)
                candidates.append(ObservationCandidate(
                    natural_key=f"{SOURCE_ID}/{geoid}/{code}/2019-2023", provenance=provenance,
                    metric_code=code, metric_label=metric["label"], aggregation=metric["aggregation"],
                    estimate=estimate, margin_of_error=moe,
                    measurement=Measurement(
                        claim_class="reported", value_state=estimate.value_state,
                        value=estimate.value, reason=estimate.reason, unit=metric["unit"],
                        universe=metric["universe"], geography_id=geoid,
                        geography_vintage="2023", reference_period="2019-2023", synthetic=synthetic),
                    locator=ApiLocator(row=row_index, geography_id=geoid, fields=tuple(
                        metric[key] for key in ("estimate", "margin_of_error",
                                                "estimate_annotation", "margin_of_error_annotation")))))
        return CandidateBatch(candidates=candidates)
    except SourceValidationError as exc:
        return failure(exc.code, str(exc))
    except (UnicodeError, tomllib.TOMLDecodeError, json.JSONDecodeError, ValidationError,
            TypeError, AttributeError, KeyError, ValueError, RecursionError):
        return failure("malformed_source", "Malformed ACS bytes or source specification")
