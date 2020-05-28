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
from immuni_exposure_ingestion.celery import celery_app
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload

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

    Upload.delete_older_than(reference_date)
    BatchFile.delete_older_than(reference_date)
