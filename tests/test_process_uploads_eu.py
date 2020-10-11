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
from immuni_common.models.mongoengine.batch_file_eu import BatchFileEu
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.lock import LockException, lock_concurrency
from immuni_exposure_ingestion.models.upload_eu import UploadEu
from immuni_exposure_ingestion.protobuf.helpers.generate_zip import batch_to_sdk_zip_file
from immuni_exposure_ingestion.protobuf.models.schema_v1_pb2 import (
    TEKSignatureList,
    TemporaryExposureKeyExport,
)
from immuni_exposure_ingestion.tasks.process_uploads_eu import _process_uploads_eu
from tests.fixtures.external_signature import mock_external_response
from tests.fixtures.upload import generate_random_uploads_eu


async def test_lock_eu() -> None:
    async with lock_concurrency("test"):
        assert True
        with raises(LockException):
            async with lock_concurrency("test"):
                assert False


@mock_config(config, "MAX_KEYS_PER_BATCH", 100)
@mock_config(config, "BATCH_EU_PERIODICITY_CRONTAB", "0 */4 * * *")
@mock_config(config, "MAX_KEYS_PER_UPLOAD", 14)
@mock_config(config, "SIGNATURE_EXTERNAL_URL", "example.com")
@mock_config(config, "SIGNATURE_KEY_ALIAS_NAME", "alias")
async def test_process_uploads_eu_simple() -> None:
    with mock_external_response():
        current_time = datetime.utcnow()
        generate_random_uploads_eu(
            5, start_time=current_time - timedelta(hours=4), end_time=current_time,
        )

        assert BatchFileEu.objects.count() == 0

        with freeze_time(current_time), patch(
            "immuni_exposure_ingestion.tasks.process_uploads_eu._LOGGER"
        ) as mock_logger:
            await _process_uploads_eu()
            assert mock_logger.warning.call_count == 0

        assert BatchFileEu.objects.count() == 1

        batch_file_eu = BatchFileEu.objects.first()
        assert batch_file_eu.index == 1
        # with respect to the _process_upload with should obtain 14*5 keys because we did not perform any validation,
        # we accept all the TEKs
        assert len(batch_file_eu.keys) == 70

        assert batch_file_eu.sub_batch_index == 1
        assert batch_file_eu.sub_batch_count == 1

        zipfile = ZipFile(BytesIO(batch_to_sdk_zip_file(batch_file_eu)))
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
        assert len(export.keys) == len(batch_file_eu.keys)
        assert export.region == "222"
        assert export.start_timestamp == int(batch_file_eu.period_start.timestamp())
        assert export.end_timestamp == int(batch_file_eu.period_end.timestamp())
        assert export.batch_size == batch_file_eu.sub_batch_count
        assert export.batch_num == batch_file_eu.sub_batch_index
        for key, pb_key in zip(batch_file_eu.keys, export.keys):
            assert base64.b64decode(key.key_data) == pb_key.key_data
            assert key.rolling_start_number == pb_key.rolling_start_interval_number


@mock_config(config, "MAX_KEYS_PER_BATCH", 150)
@mock_config(config, "BATCH_EU_PERIODICITY_CRONTAB", "0 */4 * * *")
@mock_config(config, "MAX_KEYS_PER_UPLOAD", 14)
@mock_config(config, "SIGNATURE_EXTERNAL_URL", "example.com")
@mock_config(config, "SIGNATURE_KEY_ALIAS_NAME", "alias")
@pytest.mark.parametrize("prehash", [True, False])
async def test_process_uploads_eu_advanced(prehash: bool) -> None:
    """
    Simulates an increase in EU uploads so that the second period should create two batches rather
    than only one.
    """
    with mock_external_response():
        current_time = datetime.utcnow()
        generate_random_uploads_eu(
            20, start_time=current_time, end_time=current_time + timedelta(hours=4),
        )

        assert BatchFileEu.objects.count() == 0

        with freeze_time(current_time), patch(
            "immuni_exposure_ingestion.tasks.process_uploads_eu._LOGGER"
        ) as mock_logger:
            await _process_uploads_eu()
            assert mock_logger.warning.call_count == 1

        assert BatchFileEu.objects.count() == 1

        with freeze_time(current_time + timedelta(hours=4)), patch(
            "immuni_exposure_ingestion.tasks.process_uploads_eu._LOGGER"
        ) as mock_logger:
            await _process_uploads_eu()
            assert mock_logger.warning.call_count == 0

        assert BatchFileEu.objects.count() == 2

        batches_eu = list(BatchFileEu.objects.order_by("index").all())

        # Make sure the data is correct
        assert batches_eu[0].index == 1
        assert batches_eu[1].index == 2

        # 100 keys in total, first batch gets max (90), the other gets 10
        assert len(batches_eu[0].keys) == 140
        assert len(batches_eu[1].keys) == 140

        assert batches_eu[0].sub_batch_index == 1
        assert batches_eu[1].sub_batch_index == 1

        assert batches_eu[0].sub_batch_count == 1
        assert batches_eu[1].sub_batch_count == 1

        # Make sure that there are some unprocessed uploads.
        assert UploadEu.objects.filter(to_publish=True, country="DK").count() == 0
