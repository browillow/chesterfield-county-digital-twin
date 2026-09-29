import pytest
from pydantic import ValidationError

from chesterfield_twin.domain.contracts import Measurement


def test_zero_is_observed_and_suppression_is_not_zero():
    fields = dict(
        claim_class="reported",
        unit="people",
        universe="Total population",
        geography_id="51041000000",
        geography_vintage="2024",
        reference_period="2020/2024",
        synthetic=True,
    )
    assert Measurement(**fields, value_state="observed", value="0").value == "0"
    assert Measurement(**fields, value_state="suppressed", reason="Source withheld").value is None
    for bad in (
        dict(value_state="suppressed", value="0", reason="Source withheld"),
        dict(value_state="unavailable"),
        dict(value_state="observed", value="NaN"),
    ):
        with pytest.raises(ValidationError):
            Measurement(**fields, **bad)
