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

from datetime import datetime, timedelta

from bson import ObjectId
from celery import Celery
from freezegun import freeze_time

from immuni_common.helpers.tests import mock_config
from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_common.models.mongoengine.batch_file_eu import BatchFileEu
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.models.upload_eu import UploadEu
from tests.fixtures.upload import generate_random_uploads_eu
from tests.test_process_uploads import generate_random_uploads


async def generate_various_data(num_days: int) -> None:
    starting_date = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        with freeze_time(starting_date + timedelta(days=i)):
            generate_random_uploads(
                1, start_time=datetime.utcnow(), end_time=datetime.utcnow() + timedelta(days=1),
            )
            BatchFile(
                index=i,
                keys=[TemporaryExposureKey(key_data="dummy_data", rolling_start_number=12345)],
                period_start=datetime.today() - timedelta(days=1),
                period_end=datetime.today(),
                origin="IT",
            ).save()


async def generate_various_data_eu(num_days: int) -> None:
    starting_date = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        with freeze_time(starting_date + timedelta(days=i)):
            generate_random_uploads_eu(
                1, start_time=datetime.utcnow(), end_time=datetime.utcnow() + timedelta(days=1),
            )
            BatchFileEu(
                index=i,
                keys=[TemporaryExposureKey(key_data="dummy_data", rolling_start_number=12345)],
                period_start=datetime.today() - timedelta(days=1),
                period_end=datetime.today(),
                origin="DK",
            ).save()


@mock_config(config, "DATA_RETENTION_DAYS", 14)
async def test_delete_data(setup_celery_app: Celery) -> None:
    from immuni_exposure_ingestion.tasks.delete_old_data import delete_old_data

    await generate_various_data(num_days=30)

    ref_id = ObjectId.from_datetime(datetime.utcnow() - timedelta(days=14, seconds=1))
    assert BatchFile.objects.filter(id__lte=ref_id).count() == 16
    assert Upload.objects.filter(id__lt=ref_id).count() == 16

    delete_old_data.delay()
    # Make sure there are no uploads / batches older than 14 days.
    assert BatchFile.objects.filter(id__lte=ref_id).count() == 0
    assert Upload.objects.filter(id__lte=ref_id).count() == 0


# test to delete data coming from European federation gateway service
@mock_config(config, "DATA_RETENTION_DAYS", 14)
async def test_delete_data_eu(setup_celery_app: Celery) -> None:
    from immuni_exposure_ingestion.tasks.delete_old_data import delete_old_data

    await generate_various_data_eu(num_days=30)

    ref_id = ObjectId.from_datetime(datetime.utcnow() - timedelta(days=14, seconds=1))
    # Make sure there is the exact numbers of uploads / batches in EU collection
    assert BatchFileEu.objects.filter(id__lte=ref_id).count() == 16
    assert UploadEu.objects.filter(id__lt=ref_id).count() == 16

    delete_old_data.delay()
    # Make sure there are no uploads / batches EU older than 14 days
    assert BatchFileEu.objects.filter(id__lte=ref_id).count() == 0
    assert UploadEu.objects.filter(id__lte=ref_id).count() == 0
