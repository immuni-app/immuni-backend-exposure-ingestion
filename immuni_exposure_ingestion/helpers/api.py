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
from functools import wraps
from typing import Any, Callable, Coroutine

from sanic.response import HTTPResponse

from immuni_common.core.exceptions import ApiException, UnauthorizedOtpException
from immuni_common.helpers.otp import key_for_otp_sha
from immuni_common.models.dataclasses import OtpData
from immuni_common.models.marshmallow.schemas import OtpDataSchema
from immuni_exposure_ingestion.core.managers import managers
from immuni_exposure_ingestion.monitoring.api import CHECK_OTP_REQUESTS, UPLOAD_REQUESTS


async def validate_otp_token(otp_sha: str, delete: bool = False) -> OtpData:
    """
    Load an OtpData model from the database.

    :param otp_sha: the sha256 of the OTP code.
    :param delete: if true, deletes the key right after retrieving its content.
    :return: the deserialized OtpData model associated with the given sha256 string.
    :raises: UnauthorizedOtpException if there is no OtpData associated with the given sha256.
    """

    key = key_for_otp_sha(otp_sha)

    if not delete:
        data = await managers.otp_redis.get(key)
    else:
        pipe = managers.otp_redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        data = (await pipe.execute())[0]
    if data is None:
        raise UnauthorizedOtpException()
    return OtpDataSchema().loads(data)


def monitor_upload(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Utility function to track the metrics relative to the upload request.
    :param f: The upload function to decorate.
    :return: The decorated function
    """

    @wraps(f)
    async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
        dummy = kwargs["is_dummy"]
        province = kwargs["province"]
        try:
            response = await f(*args, **kwargs)
            UPLOAD_REQUESTS.labels(dummy, province, response.status).inc()
        except ApiException as error:
            UPLOAD_REQUESTS.labels(dummy, province, error.status_code).inc()
            raise
        return response

    return _wrapper


def monitor_check_otp(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Utility function to track the metrics relative to the check-otp request.
    :param f: The check-otp function to decorate.
    :return: The decorated function
    """

    @wraps(f)
    async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
        dummy = kwargs["is_dummy"]
        try:
            response = await f(*args, **kwargs)
            CHECK_OTP_REQUESTS.labels(dummy, response.status).inc()
        except ApiException as err:
            CHECK_OTP_REQUESTS.labels(dummy, err.status_code).inc()
            raise
        return response

    return _wrapper
