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

import json
from datetime import date
from typing import List

from immuni_common.models.dataclasses import ExposureDetectionSummary
from immuni_common.models.marshmallow.schemas import ExposureDetectionSummarySchema
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.core.managers import managers


async def store_exposure_detection_summaries(
    exposure_detection_summaries: List[ExposureDetectionSummary],
    province: str,
    symptoms_started_on: date,
) -> None:
    """
    Store the given exposure detection summaries into the Analytics Redis.

    :param exposure_detection_summaries: the summaries to be stored.
    :param province: the province associated with the summaries.
    :param symptoms_started_on: the day in which the symptoms first appeared.
    """
    await managers.analytics_redis.rpush(
        config.ANALYTICS_QUEUE_KEY,
        json.dumps(
            dict(
                version=2,
                payload=dict(
                    province=province,
                    symptoms_started_on=symptoms_started_on.isoformat(),
                    exposure_detection_summaries=ExposureDetectionSummarySchema().dump(
                        exposure_detection_summaries, many=True
                    ),
                ),
            ),
        ),
    )
