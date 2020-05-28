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

import logging
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncIterator, Type

from immuni_common.core.exceptions import ImmuniException
from immuni_exposure_ingestion.core.managers import managers

_LOGGER = logging.getLogger(__name__)


class LockException(ImmuniException):
    """
    Raised when failing to acquire a lock.
    """


@asynccontextmanager
async def lock_concurrency(
    identifier: str,
    exception: Type[Exception] = LockException,
    expire: timedelta = timedelta(seconds=10),
) -> AsyncIterator:
    """
    Async context manager to acquire a Redis lock during the execution of an operation.

    :param identifier: the unique identifier of the lock.
    :param exception: the exception raised when failing to acquire the lock.
    :param expire: the time after which the lock should be released.
    :return: the lock context manager.
    :raises: exception on lock acquisition failure.
    """
    key = f"~lock:{identifier}"
    pipe = managers.celery_redis.pipeline()
    pipe.setnx(key, 1)
    pipe.expire(key, expire.total_seconds())
    if not (await pipe.execute())[0]:
        _LOGGER.error("Could not acquire lock.", extra=dict(key=key))
        raise exception
    try:
        _LOGGER.info("Acquired lock.", extra=dict(key=key))
        yield
    finally:
        _LOGGER.info("Releasing lock.", extra=dict(key=key))
        await managers.celery_redis.delete(key)
