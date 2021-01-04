#   Copyright (C) 2020 Presidenza del Consiglio dei Ministri.
#   Please refer to the AUTHORS file for more information.
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#   You should have received a copy of the GNU Affero General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/>.

from aioredis.commands import StringCommandsMixin

from immuni_common.core.exceptions import OtpCollisionException
from immuni_common.models.dataclasses import OtpData
from immuni_common.models.marshmallow.schemas import OtpDataSchema
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.core.managers import managers


async def store(cun_sha: str, cun_data: OtpData) -> None:
    """
    Store the OtpData associated with the OTP, managing the key and value dump to the database.

    :param cun_sha: the CUN associated with the database entry.
    :param cun_data: the OtpData to store.
    :raises: OtpCollision if the CUN is already in the database.
    """
    did_set = await managers.otp_redis.set(
        key=cun_sha,
        value=OtpDataSchema().dumps(cun_data),
        expire=config.OTP_EXPIRATION_SECONDS,
        exist=StringCommandsMixin.SET_IF_NOT_EXIST,
    )
    if not did_set:
        raise OtpCollisionException()
