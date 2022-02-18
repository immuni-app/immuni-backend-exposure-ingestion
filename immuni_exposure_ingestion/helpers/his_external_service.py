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
from typing import Any, Dict

import requests

from immuni_common.core.exceptions import (
    ApiException,
    DgcNotFoundException,
    OtpCollisionException,
    SchemaValidationException,
    UnauthorizedOtpException,
)
from immuni_common.models.enums import TokenType
from immuni_exposure_ingestion.core import config

_LOGGER = logging.getLogger(__name__)


def verify_cun(cun_sha: str, last_his_number: str) -> dict:
    """
    Return the response after validating the CUN and the last 8 number of HIS card
    through HIS external Service.
    The request should use mutual TLS authentication.

    :param cun_sha: the unique national code in sha256 format released by the HIS.
    :param last_his_number: the last 8 numbers of the HIS card.
    :return: the response as dictionary.
    """
    remote_url = f"https://{config.HIS_VERIFY_EXTERNAL_URL}"

    body = dict(cun=cun_sha, last_his_number=last_his_number)

    _LOGGER.info("Requesting validation with external HIS service.", extra=body)

    response = requests.post(
        remote_url,
        json=body,
        verify=config.HIS_SERVICE_CA_BUNDLE,
        cert=config.HIS_SERVICE_CERTIFICATE,
    )

    if response.status_code == 400:
        _LOGGER.info("Response 400 received from external service.",)
        raise SchemaValidationException
    if response.status_code == 401:
        _LOGGER.info("Response 401 received from external service.",)
        raise UnauthorizedOtpException
    if response.status_code == 409:
        _LOGGER.info("Response 409 received from external service.",)
        raise OtpCollisionException

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as msg_error:
        _LOGGER.error(msg_error)
        raise ApiException from msg_error

    json_response = response.json()
    _LOGGER.info("Response received from external service.", extra=json_response)

    if "id_test_verification" not in json_response or "date_test" not in json_response:
        raise UnauthorizedOtpException

    if not json_response["id_test_verification"] or not json_response["date_test"]:
        raise UnauthorizedOtpException

    return json_response


def invalidate_cun(cun_sha: str, id_test_verification: str) -> bool:
    """
    Invalidate the authorized CUN through HIS external service.
    The request should use mutual TLS authentication.

    :param cun_sha: the unique national code in sha256 format released by the HIS.
    :param id_test_verification: the id of the test returned from HIS service.
    :return: boolean
    """
    remote_url = f"https://{config.HIS_INVALIDATE_EXTERNAL_URL}"

    body = dict(cun=cun_sha, id_test_verification=id_test_verification)

    _LOGGER.info("Requesting invalidation with external HIS service.", extra=body)

    response = requests.post(
        remote_url,
        json=body,
        verify=config.HIS_SERVICE_CA_BUNDLE,
        cert=config.HIS_SERVICE_CERTIFICATE,
    )
    if response.status_code == 400:
        _LOGGER.info("Response 400 received from external service.",)
        raise SchemaValidationException
    if response.status_code == 401:
        _LOGGER.info("Response 401 received from external service.",)
        raise UnauthorizedOtpException
    if response.status_code == 409:
        _LOGGER.info("Response 409 received from external service.",)
        raise OtpCollisionException

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as msg_error:
        _LOGGER.error(msg_error)
        raise ApiException from msg_error

    json_response = response.json()
    _LOGGER.info("Response received from external service.", extra=json_response)

    return True


def retrieve_dgc(
    token_code_sha: str, last_his_number: str, his_expiring_date: date, token_type: str
) -> dict:
    """
    Return the response after validating the sha256 token, the last 8 numbers and
    the expiration date of the HIS card through external PN-DGC service.
    The request should use mutual TLS authentication.

    :param token_code_sha: the token code in sha256 format.
    :param last_his_number: the last 8 numbers of the HIS card.
    :param his_expiring_date: the expiration date of the HIS card.
    :param token_type: the type of the auth code.
    :return: dict.
    """

    remote_url = f"https://{config.DGC_EXTERNAL_URL}"

    params: Dict[str, Any] = dict(
        mode="ONLY_QRCODE",
        healthInsuranceCardNumber=last_his_number,
        healthInsuranceCardDate=his_expiring_date,
    )

    if token_type != TokenType.AUTHCODE.value:
        params["sourceDocumentIDSHA256"] = token_code_sha
    else:
        params["authCodeSHA256"] = token_code_sha

    _LOGGER.info("Retrieving Digital Green Certificate with external PN-DGC service.", extra=params)

    response = requests.get(
        remote_url,
        params=params,
        verify=config.DGC_SERVICE_CA_BUNDLE,
        cert=config.DGC_SERVICE_CERTIFICATE,
    )

    if response.status_code == 400:
        _LOGGER.info("Response 400 received from PN-DGC external service.", extra=params)
        raise ApiException
    if response.status_code == 404:
        _LOGGER.info("Response 404 received from PN-DGC external service.", extra=params)
        raise DgcNotFoundException

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as msg_error:
        _LOGGER.error(msg_error)
        raise ApiException from msg_error

    json_response = response.json()
    _LOGGER.info("DGC retrieved from external service.", extra=json_response)

    if "data" not in json_response or "qrcode" not in json_response["data"]:
        raise ApiException
    if not json_response["data"]["qrcode"]:
        raise ApiException
    if "fglTipoDgc" not in json_response["data"] or not json_response["data"]["fglTipoDgc"]:
        return {"qrcode": json_response["data"]["qrcode"]}
    else:
        return {
            "qrcode": json_response["data"]["qrcode"],
            "fglTipoDgc": json_response["data"]["fglTipoDgc"],
        }
