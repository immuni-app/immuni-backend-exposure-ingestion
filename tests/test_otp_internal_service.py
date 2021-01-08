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
from datetime import date

import pytest
from hashlib import sha256

from immuni_common.core.exceptions import SchemaValidationException, OtpCollisionException, ApiException

from immuni_exposure_ingestion.helpers.otp_internal_service import enable_otp
from tests.fixtures.core import config_set
from tests.fixtures.otp_internal_service import mock_internal_otp_service_response, \
    mock_internal_otp_service_response_schema_validation, mock_internal_otp_service_response_otp_collision, \
    mock_internal_otp_service_response_api_exception


def test_otp_internal_service() -> None:
    with config_set("OTP_INTERNAL_URL", "example.com"), mock_internal_otp_service_response(
            expected_content=True
    ):
        signature = enable_otp(otp_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                               symptoms_started_on=date.today(),
                               id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
        assert signature is True


def test_otp_internal_service_schema_validation() -> None:
    with config_set("OTP_INTERNAL_URL", "example.com"), \
         mock_internal_otp_service_response_schema_validation(
            expected_content=True
    ):
        try:
            enable_otp(otp_sha=sha256("59FU".encode("utf-8")).hexdigest(),
                       symptoms_started_on=date.today(),
                       id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
        except SchemaValidationException as e:
            assert e


def test_otp_internal_service_otp_collision_exception() -> None:
    with config_set("OTP_INTERNAL_URL", "example.com"), \
         mock_internal_otp_service_response_otp_collision(
            expected_content=True
    ):
        try:
            enable_otp(otp_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                       symptoms_started_on=date.today(),
                       id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
        except OtpCollisionException as e:
            assert e


def test_otp_internal_service_api_exception() -> None:
    with config_set("OTP_INTERNAL_URL", "example.com"), \
         mock_internal_otp_service_response_api_exception(
            expected_content=True
    ):
        try:
            enable_otp(otp_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                       symptoms_started_on=date.today(),
                       id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
        except ApiException as e:
            assert e

