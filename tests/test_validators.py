from datetime import datetime, timedelta
from typing import List, Dict

import pytest
from immuni_common.helpers.tests import mock_config
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from marshmallow import ValidationError
from pytest import raises

from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.validators import TekListValidator
from tests.fixtures.upload import generate_random_key_data


@pytest.fixture()
def teks() -> List[TemporaryExposureKey]:
    starting_period = int(
        (
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            - timedelta(days=14)
        ).timestamp()
    )
    return [
        TemporaryExposureKey(
            key_data=generate_random_key_data(),
            rolling_period=144,
            rolling_start_number=starting_period + 144 * i,
        )
        for i in range(14)
    ]


async def test_tek_key_validator_pass_if_empty() -> None:
    TekListValidator().__call__([])


async def test_tek_key_validator_pass_with_correct_teks(teks: List[TemporaryExposureKey]) -> None:
    TekListValidator().__call__(teks)


@pytest.mark.parametrize("non_144_key", range(14))
async def test_tek_key_validator_fails_if_any_key_has_period_not_144(
    teks: List[TemporaryExposureKey], non_144_key: int
) -> None:
    teks[non_144_key].rolling_period = 100
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == "Some rolling values are not 144."


@mock_config(config, "MAX_KEYS_PER_UPLOAD", 13)
async def test_tek_key_validator_fails_if_too_many_teks(teks: List[TemporaryExposureKey]) -> None:
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == "Too many TEKs. (actual: 14, max_allowed: 13)"


@pytest.mark.parametrize("duplicated_index", range(1, 13))
async def test_tek_key_validator_fails_with_duplicated_start_numbers(
    teks: List[TemporaryExposureKey], duplicated_index: int
) -> None:
    teks[duplicated_index]["rolling_start_number"] = teks[0]["rolling_start_number"]
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == "Rolling start numbers are not unique"


@pytest.mark.parametrize("overlapping_index", range(1, 13))
async def test_tek_key_validator_fails_with_overlapping_periods(
    teks: List[TemporaryExposureKey], overlapping_index: int
) -> None:
    teks[overlapping_index]["rolling_start_number"] = teks[0]["rolling_start_number"] + 1
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == "Overlapping rolling start numbers"
