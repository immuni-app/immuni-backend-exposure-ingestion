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
import random
from datetime import date, datetime, timedelta
from typing import Iterable

from freezegun import freeze_time

from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.models.upload import Upload


def generate_random_key_data(size_bytes: int = 16) -> str:
    return base64.b64encode(
        bytes(bytearray(random.getrandbits(8) for _ in range(size_bytes)))
    ).decode("utf-8")


def generate_batch_of_keys(n: int = 14) -> Iterable[TemporaryExposureKey]:
    """
    Returns a list of temporary exposure keys, one per day starting from now.
    :param n:
    :return:
    """
    starting_date = datetime.utcnow() - timedelta(days=n - 1)
    return [
        TemporaryExposureKey(
            key_data=generate_random_key_data(),
            rolling_start_number=int((starting_date + timedelta(days=day)).timestamp() / 600),
            rolling_period=144,
        )
        for day in range(config.MAX_KEYS_PER_UPLOAD)
    ]


def generate_random_uploads(n: int, *, start_time: datetime, end_time: datetime) -> None:
    """
    Generates a uniformly distributed number of uploads during the given start and end time.
    Each download will contain the maximum configured number of keys (default: 14).

    Each download will have a symptoms_started_on date of 7 days ago. This means that each upload
    should contribute to 10 keys exactly, since two days before 7 days ago is 9 days ago, and
    including today's key, we get 10 keys.
    """
    interval = timedelta(seconds=(end_time - start_time).total_seconds() / n)
    with freeze_time(start_time) as time:
        for i in range(n):
            Upload(
                to_publish=True,
                keys=generate_batch_of_keys(),
                symptoms_started_on=date.today() - timedelta(days=7),
            ).save()
            time.tick(interval)
