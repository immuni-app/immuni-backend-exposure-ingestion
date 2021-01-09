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

import logging
from datetime import date

import requests
from immuni_common.core.exceptions import SchemaValidationException, OtpCollisionException, ApiException

from immuni_exposure_ingestion.core import config

_LOGGER = logging.getLogger(__name__)


def enable_otp(otp_sha: str, symptoms_started_on: date, id_test_verification: str) -> bool:
    """
    Return the response after validating the CUN and the last 8 char of HIS card
    from external HIS Service.
    The request should use mutual TLS authentication.

    :param otp_sha: the unique national code in sha256 format released by the HIS.
    :param symptoms_started_on: the date of the first symptoms.
    :param id_test_verification: the id of the test returned from HIS service.
    :return: boolean.
    """
    remote_url = f"https://{config.OTP_INTERNAL_URL}"
    body = dict(
        otp=otp_sha,
        symptoms_started_on=symptoms_started_on.isoformat(),
        id_test_verification=id_test_verification,
    )

    _LOGGER.info("Requesting to enable the OTP with internal OTP service.", extra=body)

    response = requests.post(
        remote_url,
        json=body,
        verify=config.OTP_SERVICE_CA_BUNDLE,
        cert=config.OTP_SERVICE_CERTIFICATE,
    )

    if response.status_code == 400:
        _LOGGER.error("Response %d received from external service.",
                      response.status_code, extra=response.json())
        raise SchemaValidationException
    elif response.status_code == 409:
        _LOGGER.error("Response %d received from external service.",
                      response.status_code, extra=response.json())
        raise OtpCollisionException

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        _LOGGER.error(e)
        raise ApiException

    _LOGGER.info("Response received from internal OTP service.")
    return True
