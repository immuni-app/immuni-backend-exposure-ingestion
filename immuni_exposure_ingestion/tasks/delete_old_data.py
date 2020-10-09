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
from datetime import date, datetime, timedelta

from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_common.models.mongoengine.batch_file_eu import BatchFileEu
from immuni_exposure_ingestion.celery import celery_app
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.models.upload_eu import UploadEu
from immuni_exposure_ingestion.monitoring.celery import (
    BATCH_FILES_DELETED,
    BATCH_FILES_EU_DELETED,
    UPLOADS_DELETED,
    UPLOADS_EU_DELETED,
)

_LOGGER = logging.getLogger(__name__)


@celery_app.task
def delete_old_data() -> None:
    """
    Periodically (default: every day, at midnight) delete data older than DATA_RETENTION_DAYS days
    (default: 14).

    Deleted data comprises (i) Upload and (ii) BatchFile models.
    """
    reference_date = datetime.combine(date.today(), datetime.min.time()) - timedelta(
        days=config.DATA_RETENTION_DAYS
    )

    # Make sure there are no unprocessed uploads in the data about to be deleted.
    if Upload.unprocessed_before(reference_date):
        _LOGGER.error(
            "Some Upload objects were unprocessed until deleted! This should never happen!"
        )

    uploads_deleted = Upload.delete_older_than(reference_date)
    _LOGGER.info(
        "Upload documents deletion completed.",
        extra=dict(n_deleted=uploads_deleted, created_before=reference_date),
    )

    batches_deleted = BatchFile.delete_older_than(reference_date)
    _LOGGER.info(
        "BatchFile documents deletion completed.",
        extra=dict(n_deleted=batches_deleted, created_before=reference_date),
    )

    # Make sure there are no unprocessed uploads in the data about to be deleted.
    if UploadEu.unprocessed_before(reference_date):
        _LOGGER.error(
            "Some Upload from EU objects were unprocessed until deleted! This should never happen!"
        )

    uploads_eu_deleted = UploadEu.delete_older_than(reference_date)
    _LOGGER.info(
        "UploadEU documents deletion completed.",
        extra=dict(n_deleted=uploads_eu_deleted, created_before=reference_date),
    )

    batches_eu_deleted = BatchFileEu.delete_older_than(reference_date)
    _LOGGER.info(
        "BatchFileEU documents deletion completed.",
        extra=dict(n_deleted=batches_eu_deleted, created_before=reference_date),
    )

    UPLOADS_DELETED.inc(uploads_deleted)
    UPLOADS_EU_DELETED.inc(uploads_eu_deleted)
    BATCH_FILES_DELETED.inc(batches_deleted)
    BATCH_FILES_EU_DELETED.inc(batches_eu_deleted)
