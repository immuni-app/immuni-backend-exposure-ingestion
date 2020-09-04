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
import logging
from datetime import datetime
from io import BytesIO
from typing import List
from zipfile import ZIP_DEFLATED, ZipFile

from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_common.models.mongoengine.temporary_exposure_key import (
    TemporaryExposureKey as TemporaryExposureKeyModel,
)
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.external_signature import get_external_signature
from immuni_exposure_ingestion.protobuf.models.schema_v1_pb2 import (
    SignatureInfo,
    TEKSignature,
    TEKSignatureList,
    TemporaryExposureKey,
    TemporaryExposureKeyExport,
)

logger = logging.getLogger(__name__)


def signature_info() -> SignatureInfo:
    """
    Return a SignatureInfo object that contains information about the generated signature.
    NOTE: This contains dummy data since the specifics for the signature are not available yet.

    :return: a SignatureInfo object.
    """
    return SignatureInfo(
        app_bundle_id=config.APP_BUNDLE_ID,
        verification_key_version=config.VERIFICATION_KEY_VERSION,
        verification_key_id=config.VERIFICATION_KEY_ID,
        signature_algorithm="1.2.840.10045.4.3.2",
    )


def export_batch_file_to_bin_content(
    keys: List[TemporaryExposureKeyModel],
    period_start: datetime,
    period_end: datetime,
    sub_batch_index: int,
    sub_batch_count: int,
) -> bytes:
    """
    Transform a BatchFile into the binary content for the 'export.bin' file that will be fed to
    the Mobile Client SDK.

    Documentation here:
    https://developer.apple.com/documentation/exposurenotification/setting_up_an_exposure_notification_server

    :param batch_file: the BatchFile to transform.
    :return: the bytes that will be populate the 'export.bin' file.
    """
    content = config.EXPORT_BIN_HEADER.ljust(16, " ").encode("utf-8")

    # Compose the TEK Export protobuf object.
    export = TemporaryExposureKeyExport(
        start_timestamp=int(period_start.timestamp()),
        end_timestamp=int(period_end.timestamp()),
        region=config.REGION,
        signature_infos=[signature_info()],
        batch_num=sub_batch_index,
        batch_size=sub_batch_count,
        keys=[
            TemporaryExposureKey(
                key_data=base64.b64decode(key.key_data),
                transmission_risk_level=key.transmission_risk_level.value,
                rolling_start_interval_number=key.rolling_start_number,
                rolling_period=key.rolling_period,
            )
            for key in keys
        ],
    )

    content += export.SerializeToString()  # Despite the name this serializes in binary, not string.
    return content


def signature_content(bin_content: bytes, sub_batch_index: int, sub_batch_count: int,) -> bytes:
    """
    Return the protobuf serialization of the signature file, calculated for the given BatchFile.

    :param bin_content: the binary content for the 'export.bin' file.
    :param batch_file: the BatchFile for which to compute the protobuf serialization.
    :return: the content of the 'export.sig' file.
    """

    return TEKSignatureList(
        signatures=[
            TEKSignature(
                signature_info=signature_info(),
                batch_num=sub_batch_index,
                batch_size=sub_batch_count,
                signature=get_external_signature(bin_content),
            )
        ]
    ).SerializeToString()


def generate_client_content(
    keys: List[TemporaryExposureKeyModel],
    period_start: datetime,
    period_end: datetime,
    sub_batch_index: int,
    sub_batch_count: int,
) -> bytes:
    """
    Create the whole zip archive that will be fed to the Mobile Client SDK.
    NOTE: These functions will probably be updated.

    :param batch_file: the BatchFile from which the zip archive is to be created.
    :return: the zip archive to fed to the Mobile Client SDK.
    """
    archive = BytesIO()

    bin_content = export_batch_file_to_bin_content(
        keys=keys,
        period_start=period_start,
        period_end=period_end,
        sub_batch_index=sub_batch_index,
        sub_batch_count=sub_batch_count,
    )

    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zip_archive:
        # This is the structure of the zip archive that will be used by the Apple / Google APIs.
        with zip_archive.open("export.bin", "w") as export_file:
            export_file.write(bin_content)

        with zip_archive.open("export.sig", "w") as signature_file:
            signature_file.write(signature_content(bin_content, sub_batch_index, sub_batch_count))

    return bytes(archive.getbuffer())
