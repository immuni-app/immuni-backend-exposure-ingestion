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

import pytest

from immuni_exposure_ingestion.helpers.external_signature import get_external_signature
from tests.fixtures.core import config_set
from tests.fixtures.external_signature import mock_external_response


@pytest.mark.parametrize("prehash", [True, False])
def test_external_signature(prehash: bool) -> None:

    with config_set("SIGNATURE_KEY_ALIAS_NAME", "alias"), config_set(
        "SIGNATURE_EXTERNAL_SEND_PRECOMPUTED_HASH", prehash
    ), config_set("SIGNATURE_EXTERNAL_URL", "example.com"), mock_external_response(
        prehash=prehash, expected_content=b"payload"
    ):

        signature = get_external_signature(b"payload")
        assert signature == b"signature"
