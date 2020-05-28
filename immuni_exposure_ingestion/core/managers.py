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
from typing import Optional

import aioredis
from aioredis import Redis
from mongoengine import connect
from pymongo import MongoClient

from immuni_common.core.exceptions import ImmuniException
from immuni_common.core.managers import BaseManagers
from immuni_exposure_ingestion.core import config

_LOGGER = logging.getLogger(__name__)


class Managers(BaseManagers):
    """
    Collection of managers, lazily initialized.
    """

    _exposure_mongo: Optional[MongoClient] = None
    _analytics_redis: Optional[Redis] = None
    _otp_redis: Optional[Redis] = None
    _celery_redis: Optional[Redis] = None

    @property
    def exposure_mongo(self) -> MongoClient:
        """
        Return the Mongo manager.

        :return: the Mongo manager.
        :raise: ImmuniException if the manager is not initialized.
        """
        if self._exposure_mongo is None:
            raise ImmuniException("Cannot use the Mongo manager before initialising it.")
        return self._exposure_mongo

    @property
    def analytics_redis(self) -> Redis:
        """
        Return the Analytics Redis manager to store analytics.

        :return: the Analytics Redis manager to store analytics.
        :raise: ImmuniException if the manager is not initialized.
        """
        if self._analytics_redis is None:
            raise ImmuniException("Cannot use the Analytics Redis manager before initialising it.")
        return self._analytics_redis

    @property
    def otp_redis(self) -> Redis:
        """
        Return the Otp Redis manager to load OtpData.

        :return: the Otp Redis manager to load OtpData.
        :raise: ImmuniException if the manager is not initialized.
        """
        if self._otp_redis is None:
            raise ImmuniException("Cannot use the Otp Redis manager before initialising it.")
        return self._otp_redis

    @property
    def celery_redis(self) -> Redis:
        """
        Return the Celery Redis manager to store analytics.

        :return: the Celery Redis manager to store analytics.
        :raise: ImmuniException if the manager is not initialized.
        """
        if self._celery_redis is None:
            raise ImmuniException("Cannot use the Celery Redis manager before initialising it.")
        return self._celery_redis

    async def initialize(self) -> None:
        """
        Initialize managers on demand.
        """
        await super().initialize()
        self._exposure_mongo = connect(host=config.EXPOSURE_MONGO_URL)
        self._analytics_redis = await aioredis.create_redis_pool(
            address=config.ANALYTICS_BROKER_REDIS_URL,
            encoding="utf-8",
            maxsize=config.ANALYTICS_BROKER_REDIS_MAX_CONNECTIONS,
        )
        self._otp_redis = await aioredis.create_redis_pool(
            address=config.OTP_CACHE_REDIS_URL,
            encoding="utf-8",
            maxsize=config.OTP_CACHE_REDIS_MAX_CONNECTIONS,
        )
        # TODO: Evaluate using another instance.
        self._celery_redis = await aioredis.create_redis_pool(config.CELERY_BROKER_REDIS_URL)

    async def teardown(self) -> None:
        """
        Perform teardown actions (e.g., close open connections).
        """

        async def _close(redis: Redis) -> None:
            if redis is not None:
                redis.close()
                await redis.wait_closed()

        await super().teardown()
        await _close(self._otp_redis)
        await _close(self._analytics_redis)
        await _close(self._celery_redis)


managers = Managers()
