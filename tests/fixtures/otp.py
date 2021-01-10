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

from datetime import date
from hashlib import sha256

import pytest

from immuni_common.helpers.otp import key_for_otp_sha
from immuni_common.models.dataclasses import OtpData
from immuni_common.models.marshmallow.schemas import OtpDataSchema
from immuni_exposure_ingestion.core.managers import managers


@pytest.fixture()
async def otp() -> OtpData:
    # Key is 12345
    otp = OtpData(id_test_verification=None, symptoms_started_on=date.today())
    # Authorize this otp
    await managers.otp_redis.set(
        key_for_otp_sha(sha256("12345".encode("utf-8")).hexdigest()), OtpDataSchema().dumps(otp),
    )
    return otp
