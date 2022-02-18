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
from hashlib import sha256

from immuni_common.core.exceptions import (
    ApiException,
    DgcNotFoundException,
    OtpCollisionException,
    SchemaValidationException,
    UnauthorizedOtpException,
)
from immuni_exposure_ingestion.helpers.his_external_service import (
    invalidate_cun,
    retrieve_dgc,
    verify_cun,
)
from tests.fixtures.core import config_set
from tests.fixtures.his_external_service import (
    mock_external_his_service_api_exception,
    mock_external_his_service_missing_dict_keys,
    mock_external_his_service_missing_dict_values,
    mock_external_his_service_otp_collision,
    mock_external_his_service_schema_validation,
    mock_external_his_service_success,
    mock_external_his_service_unauthorized_otp,
    mock_invalidate_external_his_service_api_exception,
    mock_invalidate_external_his_service_otp_collision,
    mock_invalidate_external_his_service_schema_validation,
    mock_invalidate_external_his_service_success,
    mock_invalidate_external_his_service_unauthorized_otp,
    mock_retrieve_dgc_api_exception1,
    mock_retrieve_dgc_api_exception2,
    mock_retrieve_dgc_api_exception3,
    mock_retrieve_dgc_api_exception4,
    mock_retrieve_dgc_no_authcode_success,
    mock_retrieve_dgc_not_found,
    mock_retrieve_dgc_success,
    mock_retrieve_dgc_with_cbis_success,
    mock_retrieve_dgc_with_cbis_not_found,
)


def test_his_external_service() -> None:
    with config_set("HIS_VERIFY_EXTERNAL_URL", "example.com"), mock_external_his_service_success(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        json_response = verify_cun(
            cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
        )
        assert json_response


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


def test_his_external_service_missing_dict_values() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_missing_dict_values(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except UnauthorizedOtpException as e:
            assert e


def test_his_external_service_missing_dict_keys() -> None:
    with config_set(
        "HIS_VERIFY_EXTERNAL_URL", "example.com"
    ), mock_external_his_service_missing_dict_keys(
        expected_content="2d8af3b9-2c0a-4efc-9e15-72454f994e1f"
    ):
        try:
            verify_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(), last_his_number="12345678"
            )
        except UnauthorizedOtpException as e:
            assert e


def test_invalidate_his_external_service_success() -> None:
    with config_set(
        "HIS_INVALIDATE_EXTERNAL_URL", "example.com"
    ), mock_invalidate_external_his_service_success():
        response = invalidate_cun(
            cun_sha="b39e0733843b1b5d7",
            id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
        )
        assert response is True


def test_invalidate_his_external_service_schema_validation() -> None:
    with config_set(
        "HIS_INVALIDATE_EXTERNAL_URL", "example.com"
    ), mock_invalidate_external_his_service_schema_validation():
        try:
            invalidate_cun(
                cun_sha="b39e0733843b1b5d7",
                id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            )
        except SchemaValidationException as e:
            assert e


def test_invalidate_his_external_service_unauthorized_otp() -> None:
    with config_set(
        "HIS_INVALIDATE_EXTERNAL_URL", "example.com"
    ), mock_invalidate_external_his_service_unauthorized_otp():
        try:
            invalidate_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            )
        except UnauthorizedOtpException as e:
            assert e


def test_invalidate_his_external_service_otp_collision() -> None:
    with config_set(
        "HIS_INVALIDATE_EXTERNAL_URL", "example.com"
    ), mock_invalidate_external_his_service_otp_collision():
        try:
            invalidate_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            )
        except OtpCollisionException as e:
            assert e


def test_invalidate_his_external_service_api_exception() -> None:
    with config_set(
        "HIS_INVALIDATE_EXTERNAL_URL", "example.com"
    ), mock_invalidate_external_his_service_api_exception():
        try:
            invalidate_cun(
                cun_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                id_test_verification="2d8af3b9-2c0a-4efc-9e15-72454f994e1f",
            )
        except ApiException as e:
            assert e


def test_retrieve_dgc_success() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_success():
        response = retrieve_dgc(
            token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
            last_his_number="12345678",
            his_expiring_date=date.today(),
            token_type="authcode",
        )
        assert response


def test_retrieve_dgc_no_authcode_success() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_no_authcode_success():
        response = retrieve_dgc(
            token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
            last_his_number="12345678",
            his_expiring_date=date.today(),
            token_type="nucg",
        )
        assert response


def test_retrieve_no_dgc_exception() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_not_found():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="authcode",
            )
        except DgcNotFoundException as e:
            assert e


def test_retrieve_api_exception1() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_api_exception1():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="cun",
            )
        except ApiException as e:
            assert e


def test_retrieve_api_exception2() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_api_exception2():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="nrfe",
            )
        except ApiException as e:
            assert e


def test_retrieve_api_exception3() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_api_exception3():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="authcode",
            )
        except ApiException as e:
            assert e


def test_retrieve_api_exception4() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_api_exception4():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="authcode",
            )
        except ApiException as e:
            assert e


def test_retrieve_dgc_with_cbis_success() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_with_cbis_success():
        response = retrieve_dgc(
            token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
            last_his_number="12345678",
            his_expiring_date=date.today(),
            token_type="authcode",
        )
        assert response


def test_retrieve_no_dgc_with_cbis_exception() -> None:
    with config_set("DGC_EXTERNAL_URL", "example.com"), mock_retrieve_dgc_with_cbis_not_found():
        try:
            retrieve_dgc(
                token_code_sha=sha256("59FU36KR46".encode("utf-8")).hexdigest(),
                last_his_number="12345678",
                his_expiring_date=date.today(),
                token_type="authcode",
            )
        except DgcNotFoundException as e:
            assert e
