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

import json
from contextlib import contextmanager
from datetime import date
from hashlib import sha256
from typing import Dict, Iterator, Tuple

import responses
from requests import PreparedRequest

from immuni_exposure_ingestion.core import config


@contextmanager
def mock_internal_otp_service_success(
        expected_content: bool
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        def request_callback(request: PreparedRequest) -> Tuple[int, dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                # assert is valid payload
                assert payload == {
                    "otp": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    'symptoms_started_on': date.today().isoformat(),
                    "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                }
            # return 204 as status code.
            return (
                204,
                {},
                json.dumps(dict()),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.OTP_INTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_internal_otp_service_schema_validation(
        expected_content: bool
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        def request_callback(request: PreparedRequest) -> Tuple[int, dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "otp": sha256("59FU".encode("utf-8")).hexdigest(),
                    'symptoms_started_on': date.today().isoformat(),
                    "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                }
            # return 400 as status code.
            return (
                400,
                {},
                json.dumps(dict()),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.OTP_INTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_internal_otp_service_otp_collision(
        expected_content: bool
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        def request_callback(request: PreparedRequest) -> Tuple[int, dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "otp": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    'symptoms_started_on': date.today().isoformat(),
                    "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                }
            # return 409 as status code.
            return (
                409,
                {},
                json.dumps(dict()),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.OTP_INTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_internal_otp_service_api_exception(
        expected_content: bool
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        def request_callback(request: PreparedRequest) -> Tuple[int, dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "otp": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    'symptoms_started_on': date.today().isoformat(),
                    "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                }
            # return 500 as status code.
            return (
                500,
                {},
                json.dumps(dict()),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.OTP_INTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield
