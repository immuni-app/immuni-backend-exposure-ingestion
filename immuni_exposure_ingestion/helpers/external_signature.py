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

from __future__ import annotations

import base64
import logging
from hashlib import sha256

import requests

from immuni_exposure_ingestion.core import config

_LOGGER = logging.getLogger(__name__)


def get_external_signature(payload: bytes) -> bytes:
    """
    Return the signature from the external system.
    The request should use mutual TLS authentication.

    :param payload: the payload to construct the body to request the signature.
    :return: the signature.
    """
    remote_url = f"https://{config.SIGNATURE_EXTERNAL_URL}/sign/{config.SIGNATURE_KEY_ALIAS_NAME}"
    payload_input = base64.b64encode(
        sha256(payload).digest() if config.SIGNATURE_EXTERNAL_SEND_PRECOMPUTED_HASH else payload
    ).decode("utf-8")
    body = dict(prehashed=config.SIGNATURE_EXTERNAL_SEND_PRECOMPUTED_HASH, input=payload_input)

    _LOGGER.info("Requesting signature with external service.", extra=body)

    response = requests.post(
        remote_url,
        json=body,
        verify=config.SIGNATURE_SERVICE_CA_BUNDLE,
        cert=config.SIGNATURE_SERVICE_CERTIFICATE,
    )
    response.raise_for_status()
    json_response = response.json()
    _LOGGER.info("Response received from external service.", extra=json_response)
    return base64.b64decode(json_response["signature"])
