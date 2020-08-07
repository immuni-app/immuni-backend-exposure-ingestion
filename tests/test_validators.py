from datetime import datetime, timedelta
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from marshmallow import ValidationError
from pytest import raises

from immuni_common.helpers.tests import mock_config
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.temporary_exposure_key import (
    _datetime_to_rolling_start_number,
    today_midnight_rolling_start_number,
)
from immuni_exposure_ingestion.models.validators import (
    _ROLLING_PERIOD_MAX,
    _ROLLING_PERIOD_MIN,
    TekListValidator,
)
from tests.fixtures.upload import generate_random_key_data


@pytest.fixture()
def teks() -> List[TemporaryExposureKey]:
    starting_period = _datetime_to_rolling_start_number(
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=14)
    )
    return [
        TemporaryExposureKey(
            key_data=generate_random_key_data(),
            rolling_period=144,
            rolling_start_number=starting_period + 144 * i,
        )
        for i in range(15)
    ]


async def test_tek_key_validator_pass_if_empty() -> None:
    TekListValidator().__call__([])


@pytest.mark.parametrize(
    "key_index, out_of_range_rolling_period",
    (
        (key_index, out_of_range_rolling_period)
        for key_index in range(15)
        for out_of_range_rolling_period in {
            -1,
            _ROLLING_PERIOD_MIN - 1,
            _ROLLING_PERIOD_MAX + 1,
            1024,
        }
    ),
)
async def test_tek_key_validator_fails_on_out_of_range_rolling_period(
    teks: List[TemporaryExposureKey], key_index: int, out_of_range_rolling_period: int
) -> None:
    teks[key_index].rolling_period = out_of_range_rolling_period
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == (
        f"Some rolling_period values are not in "
        f"[{_ROLLING_PERIOD_MIN},{_ROLLING_PERIOD_MAX}] (e.g., {out_of_range_rolling_period})."
    )


async def test_tek_key_validator_fails_on_future_rolling_start_number(
    teks: List[TemporaryExposureKey],
) -> None:
    for tek in teks:
        tek.rolling_start_number += 144
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == (
        f"Some rolling_start_number values are in the future "
        f"(e.g., {teks[-1].rolling_start_number})."
    )


async def test_tek_key_validator_pass_with_correct_teks(teks: List[TemporaryExposureKey]) -> None:
    TekListValidator().__call__(teks)


@mock_config(config, "MAX_KEYS_PER_UPLOAD", 3)
async def test_tek_key_validator_fails_if_too_many_teks(teks: List[TemporaryExposureKey]) -> None:
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert err.value.messages[0] == f"Too many TEKs. (actual: {len(teks)}, max_allowed: 3)."


@pytest.mark.parametrize("duplicated_index", range(1, 13))
async def test_tek_key_validator_fails_with_duplicated_start_number_and_rolling_period(
    teks: List[TemporaryExposureKey], duplicated_index: int
) -> None:
    teks[duplicated_index]["rolling_start_number"] = teks[0]["rolling_start_number"]
    teks[duplicated_index]["rolling_period"] = teks[0]["rolling_period"]
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert (
        err.value.messages[0] == "TEKs do not have unique (rolling_start_number, rolling_period)."
    )


@pytest.mark.parametrize("overlapping_index", range(1, 13))
async def test_tek_key_validator_fails_with_overlapping_periods(
    teks: List[TemporaryExposureKey], overlapping_index: int
) -> None:
    overlapping_start_number = teks[0]["rolling_start_number"] + 1
    teks[overlapping_index]["rolling_start_number"] = overlapping_start_number
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert (
        err.value.messages[0]
        == f"There are invalid rolling_start_number values (i.e., {overlapping_start_number})."
    )


@mock_config(config, "ALLOW_NON_CONSECUTIVE_TEKS", False)
@pytest.mark.parametrize("missing_index", range(1, 12))
async def test_tek_key_validator_fails_with_missing_teks(
    teks: List[TemporaryExposureKey], missing_index: int
) -> None:
    missing_rolling_start_number = teks[missing_index].rolling_start_number
    del teks[missing_index]
    with raises(ValidationError) as err:
        TekListValidator().__call__(teks)

    assert (
        err.value.messages[0]
        == f"Some rolling_start_numbers are missing (i.e., {missing_rolling_start_number})."
    )


@patch("immuni_exposure_ingestion.models.validators._LOGGER.info")
async def test_tek_key_validator_finds_todays_teks(
    logger: MagicMock, teks: List[TemporaryExposureKey]
) -> None:
    teks = teks[:1]
    teks[0].rolling_start_number = today_midnight_rolling_start_number()
    TekListValidator().__call__(teks)
    logger.assert_called_with(
        "There are today's TEKs. " "They could be later ignored based on a configuration variable.",
        extra=dict(
            n_teks=len(teks),
            n_valid_teks=len(teks),
            n_today_teks=len(teks),
            today_rolling_periods=list(tek.rolling_period for tek in teks),
            EXCLUDE_CURRENT_DAY_TEK=config.EXCLUDE_CURRENT_DAY_TEK,
        ),
    )
