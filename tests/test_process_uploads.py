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

import base64
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from freezegun import freeze_time
from pytest import raises

from immuni_common.helpers.tests import mock_config
from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.lock import LockException, lock_concurrency
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.protobuf.helpers.generate_zip import batch_to_sdk_zip_file
from immuni_exposure_ingestion.protobuf.models.schema_v1_pb2 import (
    TEKSignatureList,
    TemporaryExposureKeyExport,
)
from immuni_exposure_ingestion.tasks.process_uploads import _process_uploads
from tests.fixtures.external_signature import mock_external_response
from tests.fixtures.upload import generate_random_uploads, generate_random_uploads_eu_to_it


async def test_lock() -> None:
    async with lock_concurrency("test"):
        assert True
        with raises(LockException):
            async with lock_concurrency("test"):
                assert False


@mock_config(config, "MAX_KEYS_PER_BATCH", 100)
@mock_config(config, "BATCH_PERIODICITY_CRONTAB", "0 */4 * * *")
@mock_config(config, "MAX_KEYS_PER_UPLOAD", 14)
@mock_config(config, "SIGNATURE_EXTERNAL_URL", "example.com")
@mock_config(config, "SIGNATURE_KEY_ALIAS_NAME", "alias")
@mock_config(config, "EXCLUDE_CURRENT_DAY_TEK", False)
async def test_process_uploads_simple() -> None:
    with mock_external_response():
        current_time = datetime.utcnow()
        generate_random_uploads(
            5, start_time=current_time - timedelta(hours=4), end_time=current_time,
        )
        # generate sample uploads coming from European federation gateway service and to be sent
        # to all Italian users, useful to test also the _batch_eu method inside the
        # process_upload task
        generate_random_uploads_eu_to_it(
            1, start_time=current_time, end_time=current_time + timedelta(hours=4),
        )

        assert BatchFile.objects.count() == 0

        with freeze_time(current_time), patch(
            "immuni_exposure_ingestion.tasks.process_uploads._LOGGER"
        ) as mock_logger:
            await _process_uploads()
            assert mock_logger.warning.call_count == 0

        assert BatchFile.objects.count() == 2

        batch_file = BatchFile.objects.first()
        assert batch_file.index == 1
        assert len(batch_file.keys) == 50

        assert batch_file.sub_batch_index == 1
        assert batch_file.sub_batch_count == 1

        zipfile = ZipFile(BytesIO(batch_to_sdk_zip_file(batch_file)))
        assert zipfile.namelist() == ["export.bin", "export.sig"]

        # Signature is mocked
        content = zipfile.read("export.sig")
        signatures = TEKSignatureList()
        signatures.ParseFromString(content)
        assert signatures.signatures[0].signature == b"signature"

        # Make sure the export signature contains the correct header and content
        content = zipfile.read("export.bin")
        header = content[:16].decode("utf-8")

        # Hardcoded header
        assert header.strip() == config.EXPORT_BIN_HEADER
        export = TemporaryExposureKeyExport()
        export.ParseFromString(content[16:])
        assert len(export.keys) == len(batch_file.keys)
        assert export.region == "222"
        assert export.start_timestamp == int(batch_file.period_start.timestamp())
        assert export.end_timestamp == int(batch_file.period_end.timestamp())
        assert export.batch_size == batch_file.sub_batch_count
        assert export.batch_num == batch_file.sub_batch_index
        for key, pb_key in zip(batch_file.keys, export.keys):
            assert base64.b64decode(key.key_data) == pb_key.key_data
            assert key.rolling_start_number == pb_key.rolling_start_interval_number


@mock_config(config, "MAX_KEYS_PER_BATCH", 90)
@mock_config(config, "BATCH_PERIODICITY_CRONTAB", "0 */4 * * *")
@mock_config(config, "MAX_KEYS_PER_UPLOAD", 14)
@mock_config(config, "SIGNATURE_EXTERNAL_URL", "example.com")
@mock_config(config, "SIGNATURE_KEY_ALIAS_NAME", "alias")
@mock_config(config, "EXCLUDE_CURRENT_DAY_TEK", False)
@pytest.mark.parametrize("prehash", [True, False])
async def test_process_uploads_advanced(prehash: bool) -> None:
    """
    Simulates an increase in uploads so that the second period should create two batches rather
    than only one.
    """
    with mock_external_response():
        current_time = datetime.utcnow()
        generate_random_uploads(
            20, start_time=current_time, end_time=current_time + timedelta(hours=4),
        )
        # generate sample uploads coming from European federation gateway service and to be sent
        # to all Italian users, useful to test also the _batch_eu method inside the
        # process_upload task
        generate_random_uploads_eu_to_it(
            5, start_time=current_time, end_time=current_time + timedelta(hours=4),
        )

        assert BatchFile.objects.count() == 0

        with freeze_time(current_time), patch(
            "immuni_exposure_ingestion.tasks.process_uploads._LOGGER"
        ) as mock_logger:
            await _process_uploads()
            assert mock_logger.warning.call_count == 1

        assert BatchFile.objects.count() == 2

        with freeze_time(current_time + timedelta(hours=4)), patch(
            "immuni_exposure_ingestion.tasks.process_uploads._LOGGER"
        ) as mock_logger:
            await _process_uploads()
            assert mock_logger.warning.call_count == 1

        assert BatchFile.objects.count() == 3

        batches = list(BatchFile.objects.order_by("index").all())

        # Make sure the data is correct
        assert batches[0].index == 1
        assert batches[1].index == 2

        # 100 keys in total, first batch gets max (90), the other gets 10
        assert len(batches[0].keys) == 80
        assert len(batches[1].keys) == 70

        assert batches[0].sub_batch_index == 1
        assert batches[1].sub_batch_index == 1

        assert batches[0].sub_batch_count == 1
        assert batches[1].sub_batch_count == 1

        # Make sure that there are some unprocessed uploads.
        assert Upload.objects.filter(to_publish=True).count() == 4


@mock_config(config, "MAX_KEYS_PER_BATCH", 100)
@mock_config(config, "BATCH_PERIODICITY_CRONTAB", "0 */4 * * *")
@mock_config(config, "MAX_KEYS_PER_UPLOAD", 14)
@mock_config(config, "SIGNATURE_EXTERNAL_URL", "example.com")
@mock_config(config, "SIGNATURE_KEY_ALIAS_NAME", "alias")
@mock_config(config, "EXCLUDE_CURRENT_DAY_TEK", True)
async def test_process_uploads_does_not_include_todays_keys() -> None:
    with mock_external_response():
        current_time = datetime.utcnow()
        generate_random_uploads(
            5, start_time=current_time - timedelta(hours=4), end_time=current_time,
        )
        # generate sample uploads coming from European federation gateway service and to be sent
        # to all Italian users, useful to test also the _batch_eu method inside the
        # process_upload task
        generate_random_uploads_eu_to_it(
            5, start_time=current_time, end_time=current_time + timedelta(hours=4),
        )

        assert BatchFile.objects.count() == 0

        with freeze_time(current_time), patch(
            "immuni_exposure_ingestion.tasks.process_uploads._LOGGER"
        ) as mock_logger:
            await _process_uploads()
            assert mock_logger.warning.call_count == 0

        assert BatchFile.objects.count() == 2

        batch_file = BatchFile.objects.first()

        today_rolling_start_number = int(
            current_time.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            / timedelta(minutes=10).total_seconds()
        )

        assert len(batch_file.keys) == 45

        assert all(key.rolling_start_number < today_rolling_start_number for key in batch_file.keys)
