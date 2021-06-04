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
from typing import Dict, Iterator, Optional, Tuple
from urllib.parse import urlencode

import responses
from requests import PreparedRequest

from immuni_exposure_ingestion.core import config


@contextmanager
def mock_external_his_service_success(expected_content: Optional[str] = None) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                # assert is a valid cun and valid last 8 numbers of HIS card.
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 200 as status code.
            return (
                200,
                {},
                json.dumps(
                    dict(
                        id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                        id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                        date_test="2021-01-10",
                    )
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_schema_validation(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                # assert is an invalid cun or invalid last 8 numbers of HIS card.
                assert payload == {
                    "cun": "b39e0733843b1b5d7",
                    "last_his_number": "12345678",
                }
            # return 400 as status code.
            return (
                400,
                {},
                json.dumps(
                    dict(response_code=400, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_unauthorized_otp(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                # assert the cun is not authorized.
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 401 as status code.
            return (
                401,
                {},
                json.dumps(
                    dict(response_code=401, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_otp_collision(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                # assert cun has been already authorized.
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 409 as status code.
            return (
                409,
                {},
                json.dumps(
                    dict(response_code=409, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_api_exception(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 500 as status code.
            return (
                500,
                {},
                json.dumps(
                    dict(response_code=500, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_missing_dict_values(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 200 as status code, but missing id_test_verification.
            return (
                200,
                {},
                json.dumps(
                    dict(
                        id_test_verification=None,
                        id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
                        date_test=None,
                    )
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_external_his_service_missing_dict_keys(
    expected_content: Optional[str] = None,
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                assert payload == {
                    "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                    "last_his_number": "12345678",
                }
            # return 200 as status code, but missing id_test_verification.
            return (
                200,
                {},
                json.dumps(dict(id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",)),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_VERIFY_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_invalidate_external_his_service_success() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            # assert is an invalid cun or invalid id_test_verification.
            assert payload == {
                "cun": "b39e0733843b1b5d7",
                "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            }
            # return 200 as status code.
            return (
                200,
                {},
                json.dumps(
                    dict(response_code=200, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_invalidate_external_his_service_schema_validation() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            # assert is an invalid cun or invalid id_test_verification.
            assert payload == {
                "cun": "b39e0733843b1b5d7",
                "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            }
            # return 400 as status code.
            return (
                400,
                {},
                json.dumps(
                    dict(response_code=400, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_invalidate_external_his_service_unauthorized_otp() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            # assert the cun is not authorized.
            assert payload == {
                "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            }
            # return 401 as status code.
            return (
                401,
                {},
                json.dumps(
                    dict(response_code=401, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_invalidate_external_his_service_otp_collision() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            # assert cun has been already authorized.
            assert payload == {
                "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            }
            # return 409 as status code.
            return (
                409,
                {},
                json.dumps(
                    dict(response_code=409, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_invalidate_external_his_service_api_exception() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            assert payload == {
                "cun": sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                "id_test_verification": "2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            }
            # return 500 as status code.
            return (
                500,
                {},
                json.dumps(
                    dict(response_code=500, id_transaction="2d8af3b9-2c0a-4efc-9e15-72454f994e1f")
                ),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}",
            callback=request_callback,
            content_type="application/json",
        )

        yield


@contextmanager
def mock_retrieve_dgc_success() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            authCodeSHA256=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 200

        mock_requests.add(
            responses.GET,
            url,
            body=json.dumps({"data": {"qrcode": "string"}}),
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield


@contextmanager
def mock_retrieve_dgc_not_found() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            authCodeSHA256=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 400

        mock_requests.add(
            responses.GET,
            url,
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield


@contextmanager
def mock_retrieve_dgc_no_authcode_success() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            sourceDocumentIDSHA256=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 200

        mock_requests.add(
            responses.GET,
            url,
            body=json.dumps({"data": {"qrcode": "string"}}),
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield


@contextmanager
def mock_retrieve_dgc_api_exception1() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            sourceDocumentIDSHA256=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 200

        mock_requests.add(
            responses.GET,
            url,
            body=json.dumps({"data_": {"qrcode": "string"}}),
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield


@contextmanager
def mock_retrieve_dgc_api_exception2() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            sourceDocumentIDSHA256="8edafc8c445aeb9b531ac14ce5d73671f1d5e97cb2f1dbdc5083c62f18ebb708",
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 500

        mock_requests.add(
            responses.GET,
            url,
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield


@contextmanager
def mock_retrieve_dgc_api_exception3() -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:
        base_url = f"https://{config.DGC_EXTERNAL_URL}"
        params = dict(
            mode="ONLY_QRCODE",
            healthInsuranceCardNumber="14345698",
            healthInsuranceCardDate=date.today().isoformat(),
            sourceDocumentIDSHA256="8edafc8c445aeb9b531ac14ce5d73671f1d5e97cb2f1dbdc5083c62f18ebb708",
        )
        url = f"{base_url}?{urlencode(params)}"
        status_code = 200

        mock_requests.add(
            responses.GET,
            url,
            body=json.dumps({"data": {"qrcode": ""}}),
            status=status_code,
            content_type="application/json",
            match_querystring=False,
        )

        yield
