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
from datetime import datetime, timedelta
from typing import Iterable

from immuni_common.models.enums import TransmissionRiskLevel
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.models.upload_eu import UploadEu

_LOGGER = logging.getLogger(__name__)


def extract_keys_with_risk_level_from_upload(upload: Upload) -> Iterable[TemporaryExposureKey]:
    """
    Return the keys of the given upload that are considered at risk of transmission.
    The algorithm currently considers at maximum risk all of the keys created after two days before
    the symptoms started.

    It will also remove any keys that might still be valid.

    :param upload: the upload whose keys are to be extracted from.
    :return: the list of the given upload's keys that are considered at risk of transmission.
    """

    first_risky_time = upload.symptoms_started_on - timedelta(
        days=config.DAYS_BEFORE_SYMPTOMS_TO_CONSIDER_KEY_AT_RISK
    )

    keys_at_risk = [key for key in upload.keys if key.created_at.date() >= first_risky_time]

    for key in keys_at_risk:
        key.transmission_risk_level = TransmissionRiskLevel.highest

    # TODO: Handle current day TEKs (if any) instead of discarding them.
    keys_at_risk_filtered = (
        [key for key in keys_at_risk if key.expires_at < datetime.utcnow()]
        if config.EXCLUDE_CURRENT_DAY_TEK
        else keys_at_risk
    )

    _LOGGER.info(
        "Extracting keys at risk from upload.",
        extra=dict(
            upload_id=str(upload.id),
            symptoms_started_on=upload.symptoms_started_on,
            first_risky_time=first_risky_time,
            n_keys_upload=len(upload.keys),
            n_keys_at_risk=len(keys_at_risk),
            n_keys_at_risk_filtered=len(keys_at_risk_filtered),
        ),
    )

    return keys_at_risk_filtered


def extract_keys_with_risk_level_from_upload_eu(upload: UploadEu) -> Iterable[TemporaryExposureKey]:
    """
    Return the keys of the given upload that are considered at risk of transmission.
    The algorithm currently considers at maximum risk all of the keys created after two days before
    the symptoms started.

    It will also remove any keys that might still be valid.

    :param upload: the upload whose keys are to be extracted from.
    :return: the list of the given upload's keys that are considered at risk of transmission.
    """

    first_risky_time = upload.symptoms_started_on - timedelta(
        days=config.DAYS_BEFORE_SYMPTOMS_TO_CONSIDER_KEY_AT_RISK
    )

    keys_at_risk = [key for key in upload.keys if key.created_at.date() >= first_risky_time]

    for key in keys_at_risk:
        key.transmission_risk_level = TransmissionRiskLevel.highest

    # TODO: Handle current day TEKs (if any) instead of discarding them.
    keys_at_risk_filtered = (
        [key for key in keys_at_risk if key.expires_at < datetime.utcnow()]
        if config.EXCLUDE_CURRENT_DAY_TEK
        else keys_at_risk
    )

    _LOGGER.info(
        "Extracting keys at risk from upload.",
        extra=dict(
            upload_id=str(upload.id),
            symptoms_started_on=upload.symptoms_started_on,
            first_risky_time=first_risky_time,
            n_keys_upload=len(upload.keys),
            n_keys_at_risk=len(keys_at_risk),
            n_keys_at_risk_filtered=len(keys_at_risk_filtered),
        ),
    )

    return keys_at_risk_filtered
