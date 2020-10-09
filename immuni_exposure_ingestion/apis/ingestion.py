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

import logging
from http import HTTPStatus
from typing import List

from marshmallow import ValidationError, fields
from marshmallow.validate import Regexp
from sanic import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic_openapi import doc

from immuni_common.core.exceptions import SchemaValidationException, UnauthorizedOtpException
from immuni_common.helpers.cache import cache
from immuni_common.helpers.sanic import handle_dummy_requests, validate
from immuni_common.helpers.swagger import doc_exception
from immuni_common.helpers.utils import WeightedPayload
from immuni_common.models.dataclasses import ExposureDetectionSummary
from immuni_common.models.enums import Location
from immuni_common.models.marshmallow.fields import Province
from immuni_common.models.marshmallow.schemas import (
    ExposureDetectionSummarySchema,
    TemporaryExposureKeySchema,
)
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_common.models.swagger import HeaderImmuniContentTypeJson
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.api import validate_otp_token
from immuni_exposure_ingestion.helpers.exposure_data import store_exposure_detection_summaries
from immuni_exposure_ingestion.helpers.upload import slow_down_request, validate_token_format
from immuni_exposure_ingestion.models.swagger import (
    CheckOtp,
    HeaderImmuniAuthorizationOtpSha,
    HeaderImmuniClientClock,
    HeaderImmuniDummyData,
)
from immuni_exposure_ingestion.models.swagger import Upload as UploadDoc
from immuni_exposure_ingestion.models.upload import Upload
from immuni_exposure_ingestion.models.validators import TekListValidator
from immuni_exposure_ingestion.monitoring.api import SUMMARIES_PROCESSED
from immuni_exposure_ingestion.monitoring.helpers import monitor_check_otp, monitor_upload

_LOGGER = logging.getLogger(__name__)

bp = Blueprint("ingestion", url_prefix="ingestion")


@bp.route("/upload", version=1, methods=["POST"])
@doc.summary("Upload TEKs (caller: Mobile Client).")
@doc.description(
    "Once it has validated the OTP, the Mobile Client uploads its TEKs for the past 14 days, "
    "together with the user’s Province of Domicile. "
    "If any Epidemiological Infos from the previous 14 days are available, the Mobile Client "
    "uploads those too. "
    "The timestamp that accompanies each TEK is referred to the Mobile Client’s system time. "
    "For this reason, the Mobile Client informs the Exposure Ingestion Service about its system "
    "time so that a skew can be corrected. "
    "Using the dedicated request header, the Mobile Client can indicate to the server that the "
    "call it is making is a dummy one. "
    "The server will ignore the content of such calls."
)
@doc.consumes(
    UploadDoc, location="body", required=True, content_type="application/json; charset=utf-8"
)
@doc.consumes(HeaderImmuniDummyData(), location="header", required=True)
@doc.consumes(HeaderImmuniClientClock(), location="header", required=True)
@doc.consumes(HeaderImmuniContentTypeJson(), location="header", required=True)
@doc.consumes(HeaderImmuniAuthorizationOtpSha(), location="header", required=True)
@doc_exception(SchemaValidationException)
@doc.response(
    HTTPStatus.NO_CONTENT.value, None, description="Upload completed successfully.",
)
@validate(
    location=Location.HEADERS,
    client_clock=fields.Integer(required=True, data_key=HeaderImmuniClientClock.DATA_KEY),
)
@validate(
    location=Location.JSON,
    province=Province(),
    country_of_interest=fields.List(
        fields.String(validate=Regexp(r"^[A-Z]{2}$")), required=False, missing=None
    ),
    teks=fields.Nested(
        TemporaryExposureKeySchema,
        required=True,
        many=True,
        validate=lambda x: len(x) < config.MAX_KEYS_PER_BATCH,
    ),
    exposure_detection_summaries=fields.Nested(
        ExposureDetectionSummarySchema, required=True, many=True
    ),
    padding=fields.String(validate=Regexp(rf"^[a-f0-9]{{0,{config.MAX_PADDING_SIZE}}}$")),
)
@validate_token_format
@cache(no_store=True)
@monitor_upload
# Dummy requests are currently being filtered at the reverse proxy level, emulating the same
# behavior implemented below and introducing a response delay.
# This may be re-evaluated in the future.
@handle_dummy_requests([WeightedPayload(1, HTTPResponse(status=HTTPStatus.NO_CONTENT.value))])
async def upload(  # pylint: disable=too-many-arguments
    request: Request,
    province: str,
    country_of_interest: List[str],
    teks: List[TemporaryExposureKey],
    exposure_detection_summaries: List[ExposureDetectionSummary],
    client_clock: int,
    padding: str,
) -> HTTPResponse:
    """
    Allow Mobile Clients to upload their Temporary Exposure Keys.

    :param request: the HTTP request object.
    :param province: the user's Province of Domicile.
    :param country_of_interest: the list of countries.
    :param teks: the list of TEKs.
    :param exposure_detection_summaries: the Epidemiological Info of the last 14 days, if any.
    :param client_clock: the clock on client's side, validated, but ignored.
    :param padding: the dummy data sent to protect against analysis of the traffic size.
    :return: 204 on successful upload, 400 on SchemaValidationException.
    """

    # perform consistency checks in the list of uploaded teks
    try:
        teks = TekListValidator()(teks)
    except ValidationError as exc:
        _LOGGER.error(
            "Inconsistency detected in the uploaded teks.",
            extra=dict(teks=[t.to_json() for t in teks], error=str(exc)),
        )
        # make sure not to save the inconsistent keys in the upload document
        teks = []

    upload_model = Upload(keys=teks)

    otp = await validate_otp_token(request.token, delete=True)

    upload_model.symptoms_started_on = otp.symptoms_started_on
    # for each keys add the country of interest list coming from the upload request
    for key in upload_model.keys:
        key.country_of_interest = country_of_interest

    upload_model.save()

    _LOGGER.info("Created new upload.", extra=dict(n_teks=len(teks)))

    SUMMARIES_PROCESSED.inc(len(exposure_detection_summaries))
    await store_exposure_detection_summaries(
        exposure_detection_summaries,
        province=province,
        symptoms_started_on=otp.symptoms_started_on,
    )

    return HTTPResponse(status=HTTPStatus.NO_CONTENT.value)


@bp.route("/check-otp", version=1, methods=["POST"])
@doc.summary("Check OTP (caller: Mobile Client).")
@doc.description(
    "The Mobile Client validates the OTP prior to uploading data. "
    "The request is authenticated with the OTP to be validated. "
    "Using the dedicated request header, the Mobile Client can indicate to the server that the "
    "call it is making is a dummy one. "
    "The server will ignore the content of such calls."
)
@doc.consumes(
    CheckOtp, location="body", required=True, content_type="application/json; charset=utf-8"
)
@doc.consumes(HeaderImmuniDummyData(), location="header", required=True)
@doc.consumes(HeaderImmuniContentTypeJson(), location="header", required=True)
@doc.consumes(HeaderImmuniAuthorizationOtpSha(), location="header", required=True)
@doc_exception(SchemaValidationException)
@doc_exception(UnauthorizedOtpException)
@doc.response(
    HTTPStatus.NO_CONTENT.value, None, description="Operation completed successfully.",
)
@validate(
    location=Location.JSON,
    padding=fields.String(validate=Regexp(rf"^[a-f0-9]{{0,{config.MAX_PADDING_SIZE}}}$")),
)
@validate_token_format
@slow_down_request
@cache(no_store=True)
@monitor_check_otp
# Dummy requests are currently being filtered at the reverse proxy level, emulating the same
# behavior implemented below and introducing a response delay.
# This may be re-evaluated in the future.
@handle_dummy_requests(
    [
        WeightedPayload(config.DUMMY_DATA_TOKEN_ERROR_CHANCE_PERCENT, UnauthorizedOtpException(),),
        WeightedPayload(
            100 - config.DUMMY_DATA_TOKEN_ERROR_CHANCE_PERCENT,
            HTTPResponse(status=HTTPStatus.NO_CONTENT.value),
        ),
    ]
)
async def check_otp(request: Request, padding: str) -> HTTPResponse:
    """
    Check the OTP validity, aka successfully enabled by the OTP Service.

    :param request: the HTTP request object.
    :param padding: the dummy data sent to protect against analysis of the traffic size.
    :return: 204 if the OTP is valid, 400 on SchemaValidationException, 401 on unauthorised OTP.
    """

    await validate_otp_token(request.token)
    return HTTPResponse(status=HTTPStatus.NO_CONTENT.value)
