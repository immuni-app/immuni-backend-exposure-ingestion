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

from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.celery import celery_app
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.lock import lock_concurrency
from immuni_exposure_ingestion.helpers.risk_level import (
    extract_keys_with_risk_level_from_upload,
    set_highest_risk_level,
)
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.models.upload_eu import UploadEu
from immuni_exposure_ingestion.monitoring.celery import (
    BATCH_FILES_CREATED,
    KEYS_EU_PROCESSED,
    KEYS_PROCESSED,
    UPLOADS_ENQUEUED,
    UPLOADS_EU_ENQUEUED,
)
from immuni_exposure_ingestion.protobuf.helpers.generate_zip import batch_to_sdk_zip_file

_LOGGER = logging.getLogger(__name__)


@celery_app.task()
def process_uploads() -> None:
    """
    Celery does not support async functions, so we wrap it around asyncio.run.
    """
    asyncio.run(_process_uploads())  # pragma: no cover


async def _process_uploads() -> None:
    """
    This task is run every "PERIOD".
    The period is defined in config, it can be thought of as a period of 6 / 12 / 24 hours.

    The task will create a batch file from the unprocessed Uploads of the same period, and perform
    some minor validations.

    If the number of keys in the given uploads is greater than the maximum number of keys allowed in
    a single batch, the task will create create a batch, and leave the remaining keys to be
    processed on another run of this method.
    """

    _LOGGER.info("About to start processing uploads.")
    # Acquire a lock on redis before processing anything, avoiding concurrent tasks.
    async with lock_concurrency("process_uploads"):
        _LOGGER.info("Obtained lock.")
        _create_batch_it()
        _create_batch_eu()
        _LOGGER.info("Releasing lock.")

    _LOGGER.info("Upload processing completed successfully.")


def _create_batch_it():
    """
    Get the unprocessed uploads from the upload collection, performs some validations and create
    a batch. When the maximum number of keys for a single batch is reached, create the batch,
    and leave the remaining keys to be processed on another run of this method.

    NOTE: The current maximum, and the number of nowadays keys do not require the
      generation of multiple batches in a single run of this method.
      This assumption may fall in the future, and we should monitor no queue of
      unprocessed keys will ever get stuck.
    """
    _LOGGER.info("Start processing italian TEKs.")

    infos = BatchFile.get_latest_info()
    now = datetime.utcnow()

    if infos:
        last_period, last_index = infos
    else:
        last_period = datetime.fromtimestamp(croniter(config.BATCH_PERIODICITY_CRONTAB).get_prev())
        last_index = 0

    period_start = last_period
    period_end = now

    _LOGGER.info(
        "Starting to process italian uploads.",
        extra=dict(period_start=period_start, period_end=period_end),
    )

    uploads = Upload.to_process()

    _LOGGER.info("Italian uploads have been fetched.", extra=dict(n_uploads=uploads.count()))

    processed_uploads: List[ObjectId] = []
    keys: List[TemporaryExposureKey] = []
    for upload in uploads:
        if (reached := len(keys) + len(upload.keys)) > config.MAX_KEYS_PER_BATCH:
            _LOGGER.warning(
                "Early stop: reached maximum number of keys per batch of italian uploads.",
                extra=dict(pre_reached=len(keys), reached=reached, max=config.MAX_KEYS_PER_BATCH),
            )
            break
        keys += extract_keys_with_risk_level_from_upload(upload)
        processed_uploads.append(upload.id)

    if (n_keys := len(keys)) > 0:
        # Sort the keys. This randomizes their order (since they are random strings) so that
        # keys of the same device are no more likely to end up consecutively.
        keys = sorted(keys, key=lambda x: x.key_data)

        index = last_index + 1

        batch_file = BatchFile(
            index=index,
            keys=keys,
            period_start=period_start,
            period_end=period_end,
            sub_batch_index=1,
            sub_batch_count=1,
        )
        batch_file.client_content = batch_to_sdk_zip_file(batch_file)
        batch_file.save()
        _LOGGER.info("Created new italian batch.", extra=dict(index=index, n_keys=n_keys))
        BATCH_FILES_CREATED.inc()
        KEYS_PROCESSED.inc(len(keys))

    Upload.set_published(processed_uploads)
    _LOGGER.info(
        "Flagged italian uploads as published.",
        extra=dict(n_processed_uploads=len(processed_uploads)),
    )
    UPLOADS_ENQUEUED.set(Upload.to_process().count())

    _LOGGER.info("End processing italian TEKs.")


def _create_batch_eu():
    """
    This method processes the keys of the foreign citizens that have set in their own app "Italy"
    as a country of interest. Get the unprocessed uploads downloaded from the european federation
    gateway service stored in the upload_eu collection having the country field set to "IT",
    performs some validations and create a batch. When the maximum number of keys for a single
    batch is reached, create the batch, and leave the remaining keys to be processed on another
    run of this method.

    NOTE: The current maximum, and the number of nowadays keys do not require the
      generation of multiple batches in a single run of this method.
      This assumption may fall in the future, and we should monitor no queue of
      unprocessed keys will ever get stuck.
    """
    _LOGGER.info("Start processing EU TEKs marked as italian.")

    infos = BatchFile.get_latest_info()
    now = datetime.utcnow()

    if infos:
        last_period, last_index = infos
    else:
        last_period = datetime.fromtimestamp(croniter(config.BATCH_PERIODICITY_CRONTAB).get_prev())
        last_index = 0

    period_start = last_period
    period_end = now

    _LOGGER.info(
        "Starting to process EU uploads marked as italian.",
        extra=dict(period_start=period_start, period_end=period_end),
    )

    uploads = UploadEu.to_process(country_="IT")

    _LOGGER.info(
        "EU uploads marked as italian have been fetched.", extra=dict(n_uploads=uploads.count())
    )

    processed_uploads: List[ObjectId] = []
    keys: List[TemporaryExposureKey] = []
    for upload in uploads:
        if (reached := len(keys) + len(upload.keys)) > config.MAX_KEYS_PER_BATCH:
            _LOGGER.warning(
                "Early stop: reached maximum number of keys "
                "per batch of EU uploads marked as italian.",
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

        batch_file = BatchFile(
            index=index,
            keys=keys,
            period_start=period_start,
            period_end=period_end,
            sub_batch_index=1,
            sub_batch_count=1,
            origin="EU",
            batch_tag="KEYS_EU",
        )
        batch_file.client_content = batch_to_sdk_zip_file(batch_file)
        batch_file.save()
        _LOGGER.info(
            "Created new UE batch marked as italian.", extra=dict(index=index, n_keys=n_keys)
        )
        BATCH_FILES_CREATED.inc()
        KEYS_EU_PROCESSED.inc(len(keys))

    UploadEu.set_published(processed_uploads)
    _LOGGER.info(
        "Flagged EU uploads marked as italian as published.",
        extra=dict(n_processed_uploads=len(processed_uploads)),
    )
    UPLOADS_EU_ENQUEUED.set(Upload.to_process().count())

    _LOGGER.info("End processing EU TEKs marked as italian.")
