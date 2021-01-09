#    Copyright (C) 2020 Presidenza del Consiglio dei Ministri.
#    Please refer to the AUTHORS file for more information.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.

from hashlib import sha256

import pytest

from immuni_common.core.exceptions import (
    ApiException,
    OtpCollisionException,
    SchemaValidationException,
    UnauthorizedOtpException,
)
from immuni_exposure_ingestion.helpers.his_external_service import verify_cun
from tests.fixtures.core import config_set
from tests.fixtures.his_external_service import (
    mock_external_his_service_api_exception,
    mock_external_his_service_missing_id_test_verification,
    mock_external_his_service_otp_collision,
    mock_external_his_service_schema_validation,
    mock_external_his_service_success,
    mock_external_his_service_unauthorized_otp,
)


def test_his_external_service() -> None:
    with config_set("HIS_VERIFY_EXTERNAL_URL", "example.com"), mock_external_his_service_success(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        id_verification_test = verify_cun(
            cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
        )
        assert id_verification_test == "2d8af3b9-2c0a-4efc-9e15-72454f994e1f"


def test_his_external_service_schema_validation() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_schema_validation(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(cun_sha="b39e0733843b1b5d7", last_his_number="12345678")
        except SchemaValidationException as e:
            assert e


def test_his_external_service_unauthorized_otp() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_unauthorized_otp(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except UnauthorizedOtpException as e:
            assert e


def test_his_external_service_otp_collision() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_otp_collision(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except OtpCollisionException as e:
            assert e


def test_his_external_service_api_exception() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_api_exception(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except ApiException as e:
            assert e


def test_his_external_service_missing_id_test_verification() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_missing_id_test_verification(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except UnauthorizedOtpException as e:
            assert e
