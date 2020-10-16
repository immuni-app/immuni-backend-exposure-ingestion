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
import logging
from datetime import datetime
from typing import List

from bson import ObjectId
from croniter import croniter

from immuni_common.models.mongoengine.batch_file_eu import BatchFileEu
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.celery import celery_app
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.lock import lock_concurrency
from immuni_exposure_ingestion.helpers.risk_level import set_highest_risk_level
from immuni_exposure_ingestion.models.upload_eu import UploadEu
from immuni_exposure_ingestion.monitoring.celery import (
    BATCH_FILES_EU_CREATED,
    KEYS_EU_PROCESSED,
    UPLOADS_EU_ENQUEUED,
)
from immuni_exposure_ingestion.protobuf.helpers.generate_zip import batch_to_sdk_zip_file

_LOGGER = logging.getLogger(__name__)


@celery_app.task()
def process_uploads_eu() -> None:
    """
    Celery does not support async functions, so we wrap it around asyncio.run.
    """
    asyncio.run(_process_uploads_eu())  # pragma: no cover


async def _process_uploads_eu() -> None:
    """
    This task is run every "PERIOD".
    The period is defined in config, it can be thought of as a period of 6 / 12 / 24 hours.

    The task will create a batch file from the unprocessed Uploads of the same period, and perform
    some minor validations.

    If the number of keys in the given uploads is greater than the maximum number of keys allowed in
    a single batch, the task will create create a batch, and leave the remaining keys to be
    processed on another run of this method.
    """

    _LOGGER.info("About to start processing uploads from EU.")
    # Acquire a lock on redis before processing anything, avoiding concurrent tasks.
    async with lock_concurrency("process_uploads_eu"):
        _LOGGER.info("Obtained lock.")
        for country in UploadEu.countries_to_process():
            _create_batch(country_=country)
        _LOGGER.info("Releasing lock.")

    _LOGGER.info("EU uploads processing completed successfully.")


def _create_batch(country_: str):
    """
    Get the unprocessed upload from the upload_eu collection for the country of interest,
    performs some validations and create multiple batches stored in the batch_file_eu collection.

    @param country_: the country of interest
    """
    _LOGGER.info("Start processing {} TEKs.".format(country_))

    infos = BatchFileEu.get_latest_info(country=country_)
    now = datetime.utcnow()

    if infos:
        last_period, last_index = infos
    else:
        last_period = datetime.fromtimestamp(croniter(config.BATCH_PERIODICITY_CRONTAB).get_prev())
        last_index = 0

    period_start = last_period
    period_end = now

    _LOGGER.info(
        "Starting to process {} uploads.".format(country_),
        extra=dict(period_start=period_start, period_end=period_end),
    )

    uploads = UploadEu.to_process(country_=country_)

    _LOGGER.info(
        "{} uploads have been fetched.".format(country_), extra=dict(n_uploads=uploads.count())
    )

    processed_uploads: List[ObjectId] = []
    keys: List[TemporaryExposureKey] = []
    for upload in uploads:
        if (reached := len(keys) + len(upload.keys)) > config.MAX_KEYS_PER_BATCH:
            _LOGGER.warning(
                "Early stop: reached maximum number of keys per batch of {} uploads.".format(
                    country_
                ),
                extra=dict(pre_reached=len(keys), reached=reached, max=config.MAX_KEYS_PER_BATCH),
            )
            break
        set_highest_risk_level(upload.keys)
        keys += upload.keys
        processed_uploads.append(upload.id)

    if (n_keys := len(keys)) > 0:
        # Sort the keys. This randomizes their order (since they are random strings) so that
        # keys of the same device are no more likely to end up consecutively.
        keys = sorted(keys, key=lambda x: x.key_data)

        index = last_index + 1

        batch_file = BatchFileEu(
            index=index,
            keys=keys,
            period_start=period_start,
            period_end=period_end,
            sub_batch_index=1,
            sub_batch_count=1,
            origin=country_,
        )
        batch_file.client_content = batch_to_sdk_zip_file(batch_file)
        batch_file.save()
        _LOGGER.info(
            "Created new {} batch.".format(country_), extra=dict(index=index, n_keys=n_keys)
        )
        BATCH_FILES_EU_CREATED.inc()
        KEYS_EU_PROCESSED.inc(len(keys))

    UploadEu.set_published(processed_uploads)
    _LOGGER.info(
        "Flagged {} uploads as published.".format(country_),
        extra=dict(n_processed_uploads=len(processed_uploads)),
    )
    UPLOADS_EU_ENQUEUED.set(UploadEu.to_process(country_=country_).count())

    _LOGGER.info("End processing {} TEKs.".format(country_))
