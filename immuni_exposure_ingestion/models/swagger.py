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

from sanic_openapi import doc

from immuni_common.models.swagger import UploadedTemporaryExposureKey


# TODO: add descriptions
class ExposureInfo:
    """
    Documentation class for the exposure info's entries.
    """

    date = doc.Date(required=True)
    duration = doc.Integer(required=True)
    attenuation_value = doc.Integer(required=True)
    attenuation_durations = doc.List(int, required=True)
    transmission_risk_level = doc.Integer(required=True)
    total_risk_score = doc.Integer(required=True)


# TODO: add descriptions
class ExposureDetectionSummary:
    """
    Documentation class for the exposure_detection_summaries' entries.
    """

    date = doc.Date(required=True)
    matched_key_count = doc.Integer(required=True)
    days_since_last_exposure = doc.Integer(required=True)
    attenuation_durations = doc.List(int, required=True)
    maximum_risk_score = doc.Integer(required=True)
    exposure_info = doc.List(ExposureInfo, required=True)


class HeaderImmuniAuthorizationOtpSha(doc.String):
    """
    Documentation class for the Authorization: Bearer <SHA256(OTP)> header.
    """

    def __init__(self) -> None:
        super().__init__(name="Authorization", description="Bearer <SHA256(OTP)>")


class HeaderImmuniClientClock(doc.Integer):
    """
    Documentation class for the Immuni-Client-Clock header.
    """

    DATA_KEY = "Immuni-Client-Clock"

    def __init__(self) -> None:
        super().__init__(
            name=self.DATA_KEY,
            # Backslashes needed to avoid swagger interpreting it as an html tag.
            description="\<UNIX epoch time\>",  # noqa pylint: disable=anomalous-backslash-in-string
        )


class HeaderImmuniDummyData(doc.Boolean):
    """
    Documentation class for the Immuni-Dummy-Data header.
    """

    DATA_KEY = "Immuni-Dummy-Data"

    def __init__(self) -> None:
        super().__init__(
            name=self.DATA_KEY,
            description="Whether the current request is dummy. Dummy requests are ignored.",
            choices=("true", "false"),
        )


class Upload:
    """
    Documentation class for the /v1/ingestion/upload request's body.
    """

    province = doc.String(description="The users's Province of Domicile.", required=True)
    country_of_interest = doc.List(
        str, description="The users's visited countries.", required=False
    )
    teks = doc.List(
        UploadedTemporaryExposureKey, description="The list of TEKs, maximum 14.", required=True
    )
    exposure_detection_summaries = doc.List(
        ExposureDetectionSummary,
        description="The Epidemiological Info from the previous 14 days.",
        required=True,
    )
    padding = doc.String(
        description="The dummy data sent to protect against analysis of the traffic size."
    )


class CheckOtp:
    """
    Documentation class for the /v1/ingestion/check-otp request's body.
    """

    padding = doc.String(
        description="The dummy data sent to protect against analysis of the traffic size."
    )
