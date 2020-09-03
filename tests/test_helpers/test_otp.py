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
from datetime import date, timedelta
from hashlib import sha256

from pytest import raises

from immuni_common.core.exceptions import UnauthorizedOtpException
from immuni_common.helpers.otp import key_for_otp_sha
from immuni_common.helpers.tests import generate_otp
from immuni_exposure_ingestion.core.managers import managers
from immuni_exposure_ingestion.helpers.api import validate_otp_token

_OTP = generate_otp()
_OTP_SHA = sha256(_OTP.encode("utf-8")).hexdigest()
_SYMPTOMS_STARTED_ON = date.today() - timedelta(days=30)


async def test_load_success() -> None:
    key = key_for_otp_sha(_OTP_SHA)
    await managers.otp_redis.set(
        key=key, value=json.dumps({"symptoms_started_on": _SYMPTOMS_STARTED_ON.isoformat()})
    )
    actual = await validate_otp_token(otp_sha=_OTP_SHA)
    assert actual.symptoms_started_on == _SYMPTOMS_STARTED_ON


async def test_load_success_and_delete() -> None:
    key = key_for_otp_sha(_OTP_SHA)
    await managers.otp_redis.set(
        key=key, value=json.dumps({"symptoms_started_on": _SYMPTOMS_STARTED_ON.isoformat()})
    )
    actual = await validate_otp_token(otp_sha=_OTP_SHA, delete=True)
    assert actual.symptoms_started_on == _SYMPTOMS_STARTED_ON

    assert await managers.otp_redis.get(key=key) is None


async def test_load_failure() -> None:
    with raises(UnauthorizedOtpException):
        await validate_otp_token(otp_sha=_OTP_SHA)


async def test_load_failure_delete() -> None:
    with raises(UnauthorizedOtpException):
        await validate_otp_token(otp_sha=_OTP_SHA, delete=True)
