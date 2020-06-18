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

import asyncio
from typing import Any, Tuple

from celery.signals import worker_process_init, worker_process_shutdown

from immuni_common.celery import CeleryApp, Schedule, string_to_crontab
from immuni_exposure_ingestion import tasks
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.core.managers import managers


# pylint: disable=cyclic-import,import-outside-toplevel
def _get_schedules() -> Tuple[Schedule, ...]:
    """
    Get static scheduling of tasks.
    # NOTE: Tasks need to be imported locally, so as to avoid cyclic dependencies.

    :return: the tuple of tasks schedules.
    """
    from immuni_exposure_ingestion.tasks.process_uploads import process_uploads
    from immuni_exposure_ingestion.tasks.delete_old_data import delete_old_data

    return (
        Schedule(task=process_uploads, when=string_to_crontab(config.BATCH_PERIODICITY_CRONTAB)),
        Schedule(task=delete_old_data, when=string_to_crontab(config.DELETE_OLD_DATA_CRONTAB)),
    )


@worker_process_init.connect
def worker_process_init_listener(**kwargs: Any) -> None:
    """
    Callback on worker initialization.
    """
    asyncio.run(managers.initialize())


@worker_process_shutdown.connect
def worker_process_shutdown_listener(**kwargs: Any) -> None:
    """
    Callback on worker shutdown.
    """
    asyncio.run(managers.teardown())


celery_app = CeleryApp(
    service_dir_name="immuni_exposure_ingestion",
    broker_redis_url=config.CELERY_BROKER_REDIS_URL,
    always_eager=config.CELERY_ALWAYS_EAGER,
    tasks_module=tasks,
    schedules_function=_get_schedules,
)
