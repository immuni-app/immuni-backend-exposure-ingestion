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
import json
from contextlib import contextmanager
from hashlib import sha256
from typing import Dict, Iterator, Optional, Tuple

import responses
from requests import PreparedRequest

from immuni_exposure_ingestion.core import config


@contextmanager
def mock_external_response(
    prehash: bool = False, expected_content: Optional[bytes] = None
) -> Iterator[None]:
    with responses.RequestsMock() as mock_requests:

        def request_callback(request: PreparedRequest) -> Tuple[int, Dict, str]:
            assert request.body is not None
            payload = json.loads(request.body)
            if expected_content:
                input_payload = sha256(expected_content).digest() if prehash else expected_content
                assert payload == {
                    "prehashed": prehash,
                    "input": base64.b64encode(input_payload).decode("utf-8"),
                }
            return (
                200,
                {},
                json.dumps(dict(signature=base64.b64encode(b"signature").decode("utf-8"))),
            )

        mock_requests.add_callback(
            responses.POST,
            f"https://{config.SIGNATURE_EXTERNAL_URL}/sign/{config.SIGNATURE_KEY_ALIAS_NAME}",
            callback=request_callback,
            content_type="application/json",
        )

        yield
