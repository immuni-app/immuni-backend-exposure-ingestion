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

from datetime import date, timedelta
from typing import Iterable

from immuni_common.models.enums import TransmissionRiskLevel
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload


def extract_keys_with_risk_level_from_upload(upload: Upload) -> Iterable[TemporaryExposureKey]:
    """
    Return the keys of the given upload that are considered at risk of transmission.
    The algorithm currently considers at maximum risk all of the keys created after two days before
    the symptoms started.

    We will also remove any keys created today.

    :param upload: the upload whose keys are to be extracted from.
    :return: the list of the given upload's keys that are considered at risk of transmission.
    """

    first_risky_time = upload.symptoms_started_on - timedelta(
        days=config.DAYS_BEFORE_SYMPTOMS_TO_CONSIDER_KEY_AT_RISK
    )

    keys_at_risk = [key for key in upload.keys if key.created_at.date() >= first_risky_time]

    for key in keys_at_risk:
        key.transmission_risk_level = TransmissionRiskLevel.highest

    # Also remove any keys that might still be valid
    return [key for key in keys_at_risk if key.created_at.date() < date.today()]
