from functools import wraps
from typing import Any, Callable, Coroutine

from sanic.response import HTTPResponse

from immuni_common.core.exceptions import ApiException
from immuni_common.helpers.sanic import validate
from immuni_common.models.enums import Location
from immuni_common.models.marshmallow.fields import IntegerBoolField
from immuni_common.models.swagger import HeaderImmuniDummyData
from immuni_exposure_ingestion.monitoring.api import (
    CHECK_CUN_REQUESTS,
    CHECK_OTP_REQUESTS,
    UPLOAD_REQUESTS,
)


def monitor_upload(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Decorator to monitor the metrics relative to the upload request.
    :param f: the upload function to decorate.
    :return: the decorated function.
    """

    @wraps(f)
    @validate(
        location=Location.HEADERS,
        is_dummy=IntegerBoolField(
            required=True, allow_strings=True, data_key=HeaderImmuniDummyData.DATA_KEY,
        ),
    )
    async def _wrapper(*args: Any, is_dummy: bool, **kwargs: Any) -> HTTPResponse:
        province = kwargs["province"]
        try:
            response = await f(*args, **kwargs)
            UPLOAD_REQUESTS.labels(is_dummy, province, response.status).inc()
        except ApiException as error:
            UPLOAD_REQUESTS.labels(is_dummy, province, error.status_code.value).inc()
            raise
        return response

    return _wrapper


def monitor_check_otp(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Decorator to monitor the metrics relative to the check-otp request.
    :param f: the check-otp function to decorate.
    :return: the decorated function.
    """

    @wraps(f)
    @validate(
        location=Location.HEADERS,
        is_dummy=IntegerBoolField(
            required=True, allow_strings=True, data_key=HeaderImmuniDummyData.DATA_KEY,
        ),
    )
    async def _wrapper(*args: Any, is_dummy: bool, **kwargs: Any) -> HTTPResponse:
        try:
            response = await f(*args, **kwargs)
            CHECK_OTP_REQUESTS.labels(is_dummy, response.status).inc()
        except ApiException as error:
            CHECK_OTP_REQUESTS.labels(is_dummy, error.status_code.value).inc()
            raise
        return response

    return _wrapper


def monitor_check_cun(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Decorator to monitor the metrics relative to the check-cun request.
    :param f: the check-cun function to decorate.
    :return: the decorated function.
    """

    @wraps(f)
    @validate(
        location=Location.HEADERS,
        is_dummy=IntegerBoolField(
            required=True, allow_strings=True, data_key=HeaderImmuniDummyData.DATA_KEY,
        ),
    )
    async def _wrapper(*args: Any, is_dummy: bool, **kwargs: Any) -> HTTPResponse:
        try:
            response = await f(*args, **kwargs)
            CHECK_CUN_REQUESTS.labels(is_dummy, response.status).inc()
        except ApiException as error:
            CHECK_CUN_REQUESTS.labels(is_dummy, error.status_code.value).inc()
            raise
        return response

    return _wrapper
