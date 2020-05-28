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

from asyncio import AbstractEventLoop
from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Iterator

import pytest
from celery import Celery
from mongoengine import get_db
from pytest import fixture
from pytest_sanic.utils import TestClient
from sanic import Sanic

from immuni_common.helpers.tests import create_no_expired_keys_fixture
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.core.managers import managers


@contextmanager
def config_set(name: str, value: Any) -> Iterator[None]:
    old_value = getattr(config, name)
    setattr(config, name, value)
    try:
        yield
    finally:
        setattr(config, name, old_value)


@fixture(autouse=True)
async def cleanup_db(sanic: Sanic) -> None:
    managers.exposure_mongo.drop_database(get_db().name)
    await managers.otp_redis.flushdb()
    await managers.analytics_redis.flushdb()


@fixture
async def sanic(monitoring_setup: None) -> Sanic:
    from immuni_exposure_ingestion.sanic import sanic_app

    await managers.initialize()
    yield sanic_app
    await managers.teardown()


@fixture
async def sanic_custom_client(sanic_client: TestClient) -> TestClient:
    yield sanic_client


@fixture
def client(
    loop: AbstractEventLoop,
    sanic: Sanic,
    sanic_custom_client: Callable[[Sanic], Awaitable[TestClient]],
) -> TestClient:
    return loop.run_until_complete(sanic_custom_client(sanic))


@pytest.fixture(scope="function")
def setup_celery_app(monitoring_setup: None) -> Celery:
    from immuni_exposure_ingestion.celery import celery_app

    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)
    return celery_app


@fixture(autouse=True)
def ensure_no_unexpired_keys(sanic: Sanic) -> None:
    create_no_expired_keys_fixture(managers.otp_redis)
    create_no_expired_keys_fixture(managers.analytics_redis)
