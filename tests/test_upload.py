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
import time
from copy import deepcopy
from datetime import date, datetime, timedelta
from hashlib import sha256
from http import HTTPStatus
from typing import Dict, Optional, Tuple
from unittest.mock import patch

import pytest
from pytest_sanic.utils import TestClient

from immuni_common.core.exceptions import UnauthorizedOtpException
from immuni_common.helpers.otp import key_for_otp_sha
from immuni_common.helpers.tests import mock_config
from immuni_common.models.dataclasses import OtpData
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.core.managers import managers
from immuni_exposure_ingestion.models.upload import Upload
from tests.fixtures.upload import generate_random_key_data

UPLOAD_DATA = dict(
    province="AG",
    padding="4dd16",
    exposure_detection_summaries=[
        {
            "date": date.today().isoformat(),
            "matched_key_count": 2,
            "days_since_last_exposure": 1,
            "attenuation_durations": [300, 0, 0],
            "maximum_risk_score": 4,
            "exposure_info": [
                {
                    "date": "2020-05-16",
                    "duration": 5,
                    "attenuation_value": 45,
                    "attenuation_durations": [300, 0, 0],
                    "transmission_risk_level": 1,
                    "total_risk_score": 4,
                }
            ],
        }
    ],
    teks=[
        {
            "key_data": generate_random_key_data(),
            "rolling_start_number": int((datetime.utcnow() - timedelta(days=i)).timestamp() / 600),
            "rolling_period": 144,
        }
        for i in range(14)
    ],
)

CONTENT_TYPE_HEADER = {"Content-Type": "application/json; charset=UTF-8"}


@pytest.fixture
def upload_data() -> Dict:
    return deepcopy(UPLOAD_DATA)


@pytest.fixture
def headers() -> Dict[str, str]:
    return {"Immuni-Dummy-Data": "0", "Immuni-Client-Clock": str(int(time.time()))}


@pytest.fixture
def auth_headers(headers: Dict[str, str]) -> Dict[str, str]:
    headers["Authorization"] = f"Bearer {sha256('12345'.encode('utf-8')).hexdigest()}"
    return headers


async def test_dummy_data_upload(
    client: TestClient, upload_data: Dict, auth_headers: Dict[str, str]
) -> None:
    auth_headers["Immuni-Dummy-Data"] = "1"
    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers)
    assert response.status == 204
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


async def test_dummy_data_check_otp_success(
    client: TestClient, auth_headers: Dict[str, str]
) -> None:
    auth_headers["Immuni-Dummy-Data"] = "1"
    auth_headers.update(CONTENT_TYPE_HEADER)
    with patch("immuni_common.helpers.sanic.weighted_random", side_effect=lambda x: x[1].payload):
        response = await client.post(
            "/v1/ingestion/check-otp", json=dict(padding="4dd1"), headers=auth_headers
        )
    assert response.status == 204
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


async def test_dummy_data_check_otp_fail(client: TestClient, auth_headers: Dict[str, str]) -> None:
    auth_headers["Immuni-Dummy-Data"] = "1"
    auth_headers.update(CONTENT_TYPE_HEADER)
    with patch("immuni_common.helpers.sanic.weighted_random", side_effect=lambda x: x[0].payload):
        response = await client.post(
            "/v1/ingestion/check-otp", json=dict(padding="4dd1"), headers=auth_headers
        )
    assert response.status == 401
    data = await response.json()
    assert data["message"] == UnauthorizedOtpException.error_message
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


@pytest.mark.parametrize(
    "bad_data",
    [(None, "None"), (json.dumps(dict()), "Empty Dict")]
    + [
        (json.dumps({k: v for k, v in UPLOAD_DATA.items() if k != excluded}), excluded)
        for excluded in UPLOAD_DATA
    ],
)
async def test_upload_bad_request_body(
    client: TestClient, bad_data: Tuple[str, str], headers: Dict[str, str]
) -> None:
    headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=bad_data[0], headers=headers,)
    assert response.status == 400
    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


@pytest.mark.parametrize("province", ["asd", "ROMA", None])
async def test_invalid_province(
    client: TestClient, upload_data: Dict, province: str, headers: Dict[str, str]
) -> None:
    upload_data["province"] = province
    headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=headers)
    assert response.status == 400
    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."


@pytest.mark.parametrize("dummy_header", ["other", "boh", ""])
async def test_upload_bad_request_dummy_header(
    client: TestClient, upload_data: Dict, dummy_header: str, headers: Dict[str, str]
) -> None:
    headers["Immuni-Dummy-Data"] = dummy_header
    headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=headers,)
    assert response.status == 400
    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


@pytest.mark.parametrize("endpoint", ["/v1/ingestion/upload", "/v1/ingestion/check-otp"])
@pytest.mark.parametrize("token", ["asd", "12345", "abcdefghijklmnopqrstuvwxy"])
async def test_bad_auth_token_raises_validation_error(
    client: TestClient, upload_data: Dict, auth_headers: Dict[str, str], token: str, endpoint: str
) -> None:
    auth_headers["Authorization"] = f"Bearer {token}"
    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post(endpoint, json=upload_data, headers=auth_headers)
    assert response.status == 400

    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."


@pytest.mark.parametrize("endpoint", ["/v1/ingestion/upload"])
@pytest.mark.parametrize("missing_header", ["Immuni-Dummy-Data", "Immuni-Client-Clock"])
async def test_upload_without_headers(
    client: TestClient, endpoint: str, missing_header: str, headers: Dict[str, str]
) -> None:
    del headers[missing_header]
    headers.update(CONTENT_TYPE_HEADER)
    response = await client.post(endpoint, headers=headers)
    assert response.status == 400
    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


@pytest.mark.parametrize("endpoint", ["/v1/ingestion/check-otp"])
@pytest.mark.parametrize("missing_header", ["Immuni-Dummy-Data"])
async def test_check_otp_without_headers(
    client: TestClient, endpoint: str, missing_header: str, headers: Dict[str, str]
) -> None:
    del headers[missing_header]
    headers.update(CONTENT_TYPE_HEADER)
    response = await client.post(endpoint, headers=headers)
    assert response.status == 400
    data = await response.json()
    assert data["message"] == "Request not compliant with the defined schema."
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


async def test_upload_otp_check_fail(client: TestClient, auth_headers: Dict[str, str]) -> None:
    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post(
        "/v1/ingestion/check-otp", json=dict(padding="4dd1"), headers=auth_headers,
    )
    assert response.status == 401
    data = await response.json()
    assert data["message"] == UnauthorizedOtpException.error_message
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


async def test_upload_otp_check_pass(
    client: TestClient, otp: OtpData, auth_headers: Dict[str, str]
) -> None:
    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post(
        "/v1/ingestion/check-otp", json=dict(padding="4dd1"), headers=auth_headers,
    )
    assert response.status == 204
    assert Upload.objects.count() == 0
    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 0


async def test_upload_too_many_keys(
    client: TestClient, otp: OtpData, auth_headers: Dict[str, str], upload_data: Dict,
) -> None:
    # Add 14 more keys
    for _ in range(14):
        upload_data["teks"].append(
            {
                "key_data": generate_random_key_data(),
                "rolling_start_number": 12345,
                "rolling_period": 144,
            }
        )

    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers,)
    assert response.status == 400
    assert Upload.objects.count() == 0


async def test_upload_invalid_start_numbers(
    client: TestClient, otp: OtpData, auth_headers: Dict[str, str], upload_data: Dict,
) -> None:

    upload_data["teks"][1]["rolling_start_number"] = (
        upload_data["teks"][1]["rolling_start_number"] + 10
    )

    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers,)
    assert response.status == 204
    assert Upload.objects.count() == 1
    upload = Upload.objects.first()
    # teks should be discarded, as they did not pass the teks validator
    assert not upload.keys
    assert upload.to_publish is True
    assert upload.symptoms_started_on == otp.symptoms_started_on


@pytest.mark.parametrize("length", (0, 1, 15, 17, 100))
async def test_upload_keys_with_wrong_length(
    client: TestClient, otp: OtpData, auth_headers: Dict[str, str], upload_data: Dict, length: int
) -> None:
    upload_data["teks"] = [
        {"key_data": generate_random_key_data(length), "rolling_start_number": 12345}
        for _ in range(14)
    ]

    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers)
    assert response.status == HTTPStatus.BAD_REQUEST.value


async def test_upload_keys_with_missing_teks(
    client: TestClient, otp: OtpData, auth_headers: Dict[str, str], upload_data: Dict,
) -> None:
    upload_data["teks"] = None

    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers)
    assert response.status == HTTPStatus.BAD_REQUEST.value


@mock_config(config, "ALLOW_NON_CONSECUTIVE_TEKS", True)
@pytest.mark.parametrize("include_infos", [True, False])
@pytest.mark.parametrize("include_summaries", [True, False])
@pytest.mark.parametrize("include_teks", [True, False])
@pytest.mark.parametrize("remove_tek", [None] + [*range(14)])
async def test_upload_otp_complete(
    client: TestClient,
    otp: OtpData,
    auth_headers: Dict[str, str],
    upload_data: Dict,
    include_infos: bool,
    include_summaries: bool,
    include_teks: bool,
    remove_tek: Optional[int],
) -> None:

    otp_sha = sha256("12345".encode("utf-8")).hexdigest()

    if not include_infos:
        upload_data["exposure_detection_summaries"][0]["exposure_info"] = []
    if not include_summaries:
        upload_data["exposure_detection_summaries"] = []
    if remove_tek is not None:
        del upload_data["teks"][remove_tek]
    if not include_teks:
        upload_data["teks"] = []

    auth_headers.update(CONTENT_TYPE_HEADER)
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers,)

    assert await managers.otp_redis.get(key_for_otp_sha(otp_sha)) is None

    assert response.status == 204
    assert Upload.objects.count() == 1
    upload = Upload.objects.first()
    assert upload.to_publish is True
    assert upload.symptoms_started_on == otp.symptoms_started_on

    if include_teks:
        assert len(upload.keys) == len(upload_data["teks"])
        for uploaded_tek, retrieved_tek in zip(upload_data["teks"], upload.keys):
            assert retrieved_tek.key_data == uploaded_tek["key_data"]
            assert retrieved_tek.rolling_start_number == uploaded_tek["rolling_start_number"]
            assert retrieved_tek.rolling_period == uploaded_tek["rolling_period"]
    else:
        assert upload.keys == []

    assert await managers.analytics_redis.llen(config.ANALYTICS_QUEUE_KEY) == 1
    enqueued_message = await managers.analytics_redis.lpop(config.ANALYTICS_QUEUE_KEY)
    assert enqueued_message
    content = json.loads(enqueued_message)

    assert content == dict(
        version=1,
        payload=dict(
            province="AG",
            symptoms_started_on=date.today().isoformat(),
            exposure_detection_summaries=upload_data["exposure_detection_summaries"],
        ),
    )


@pytest.mark.parametrize("invalid_padding", ["\\asd*&!@#", "a" * (config.MAX_PADDING_SIZE + 1)])
async def test_invalid_paddings_upload(
    client: TestClient,
    invalid_padding: str,
    otp: OtpData,
    auth_headers: Dict[str, str],
    upload_data: Dict,
) -> None:
    upload_data["padding"] = invalid_padding
    response = await client.post("/v1/ingestion/upload", json=upload_data, headers=auth_headers,)
    assert response.status == 400


@pytest.mark.parametrize("invalid_padding", ["\\asd*&!@#", "a" * (config.MAX_PADDING_SIZE + 1)])
async def test_invalid_paddings_check_otp(
    client: TestClient, invalid_padding: str, auth_headers: Dict[str, str],
) -> None:
    response = await client.post(
        "/v1/ingestion/check-otp", json=dict(padding=invalid_padding), headers=auth_headers,
    )
    assert response.status == 400
