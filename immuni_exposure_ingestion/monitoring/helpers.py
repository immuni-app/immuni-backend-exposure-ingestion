from functools import wraps
from typing import Any, Callable, Coroutine

from sanic.response import HTTPResponse

from immuni_common.core.exceptions import ApiException
from immuni_exposure_ingestion.monitoring.api import CHECK_OTP_REQUESTS, UPLOAD_REQUESTS


def monitor_upload(f: Callable[..., Coroutine[Any, Any, HTTPResponse]]) -> Callable:
    """
    Decorator to monitor the metrics relative to the upload request.
    :param f: the upload function to decorate.
    :return: the decorated function.
    """

    @wraps(f)
    async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
        dummy = kwargs["is_dummy"]
        province = kwargs["province"]
        try:
            response = await f(*args, **kwargs)
            UPLOAD_REQUESTS.labels(dummy, province, response.status).inc()
        except ApiException as error:
            UPLOAD_REQUESTS.labels(dummy, province, error.status_code.value).inc()
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
    async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
        dummy = kwargs["is_dummy"]
        try:
            response = await f(*args, **kwargs)
            CHECK_OTP_REQUESTS.labels(dummy, response.status).inc()
        except ApiException as error:
            CHECK_OTP_REQUESTS.labels(dummy, error.status_code.value).inc()
            raise
        return response

    return _wrapper
