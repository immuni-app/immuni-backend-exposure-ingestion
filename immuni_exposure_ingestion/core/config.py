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

from decouple import config

from immuni_common.core import config as common_config
from immuni_common.helpers.config import validate_crontab
from immuni_common.models.enums import Environment

_LOGGER = logging.getLogger(__name__)


EXPOSURE_MONGO_URL: str = config(
    "EXPOSURE_MONGO_URL", default="mongodb://localhost:27017/immuni-exposure-ingestion-dev"
)

OTP_CACHE_REDIS_URL: str = config("OTP_CACHE_REDIS_URL", default="redis://localhost:6379/0")
OTP_CACHE_REDIS_MAX_CONNECTIONS: int = config(
    "OTP_CACHE_REDIS_MAX_CONNECTIONS", default=10, cast=int
)

# Default to True as one could disable the bluetooth for more than a day.
ALLOW_NON_CONSECUTIVE_TEKS: bool = config("ALLOW_NON_CONSECUTIVE_TEKS", cast=bool, default=True)

ANALYTICS_BROKER_REDIS_URL: str = config(
    "ANALYTICS_BROKER_REDIS_URL", default="redis://localhost:6379/1"
)
ANALYTICS_BROKER_REDIS_MAX_CONNECTIONS: int = config(
    "ANALYTICS_BROKER_REDIS_MAX_CONNECTIONS", default=10, cast=int
)
ANALYTICS_QUEUE_KEY: str = config("ANALYTICS_QUEUE_KEY", default="ingested_exposure_data")

CELERY_BROKER_REDIS_URL: str = config("CELERY_BROKER_REDIS_URL", default="redis://localhost:6379/0")
CELERY_ALWAYS_EAGER: bool = config(
    "CELERY_ALWAYS_EAGER", cast=bool, default=common_config.ENV == Environment.TESTING
)

DATA_RETENTION_DAYS: int = config("DATA_RETENTION_DAYS", cast=int, default=14)

CHECK_OTP_REQUEST_TIMEOUT_MILLIS: int = config(
    "CHECK_OTP_REQUEST_TIMEOUT_MILLIS", cast=int, default=150
)
CHECK_OTP_REQUEST_TIMEOUT_SIGMA: int = config(
    "CHECK_OTP_REQUEST_TIMEOUT_SIGMA", cast=int, default=20
)

DUMMY_DATA_TOKEN_ERROR_CHANCE_PERCENT: int = config(
    "DUMMY_DATA_TOKEN_ERROR_CHANCE_PERCENT", cast=int, default=1
)

# [14 days before TEKs + (possibly) 1 current day TEK with rolling_period up until "now" = 15 TEKs]
# Yet, since the upload could fail (e.g., connection error), there could be multiple TEKs per day.
# Following Google's suggestion, some slack is given here by setting it to 30.
MAX_KEYS_PER_UPLOAD: int = config("MAX_KEYS_PER_UPLOAD", cast=int, default=30)
MAX_KEYS_PER_BATCH: int = config("MAX_KEYS_PER_BATCH", cast=int, default=10000)

DAYS_BEFORE_SYMPTOMS_TO_CONSIDER_KEY_AT_RISK: int = config(
    "DAYS_BEFORE_SYMPTOMS_TO_CONSIDER_KEY_AT_RISK", cast=int, default=2
)

APP_BUNDLE_ID: str = config("APP_BUNDLE_ID", default="it.ministerodellasalute.immuni")
ANDROID_PACKAGE: str = config("ANDROID_PACKAGE", default="it.ministerodellasalute.immuni")
REGION: str = config("REGION", default="222")

EXCLUDE_CURRENT_DAY_TEK: bool = config("EXCLUDE_CURRENT_DAY_TEK", cast=bool, default=True)
EXPORT_BIN_HEADER: str = config("EXPORT_BIN_HEADER", default="EK Export v1")

VERIFICATION_KEY_ID: str = config("VERIFICATION_KEY_ID", default="222")
VERIFICATION_KEY_VERSION: str = config("VERIFICATION_KEY_VERSION", default="v1")

SIGNATURE_KEY_ALIAS_NAME: str = config("SIGNATURE_KEY_ALIAS_NAME", default="")

SIGNATURE_EXTERNAL_SEND_PRECOMPUTED_HASH: bool = config(
    "SIGNATURE_EXTERNAL_SEND_PRECOMPUTED_HASH", cast=bool, default=False
)

HIS_VERIFY_EXTERNAL_URL: str = config("HIS_VERIFY_EXTERNAL_URL", default="")
HIS_INVALIDATE_EXTERNAL_URL: str = config("HIS_INVALIDATE_EXTERNAL_URL", default="")
HIS_SERVICE_CERTIFICATE: str = config("HIS_SERVICE_CERTIFICATE", default="")
HIS_SERVICE_CA_BUNDLE: str = config("HIS_SERVICE_CA_BUNDLE", default="")

OTP_INTERNAL_URL: str = config("OTP_INTERNAL_URL", default="")
OTP_SERVICE_CERTIFICATE: str = config("OTP_SERVICE_CERTIFICATE", default="")
OTP_SERVICE_CA_BUNDLE: str = config("OTP_SERVICE_CA_BUNDLE", default="")

SIGNATURE_EXTERNAL_URL: str = config("SIGNATURE_EXTERNAL_URL", default="")
SIGNATURE_SERVICE_CERTIFICATE: str = config("SIGNATURE_SERVICE_CERTIFICATE", default="")
SIGNATURE_SERVICE_CA_BUNDLE: str = config("SIGNATURE_SERVICE_CA_BUNDLE", default="")

DGC_EXTERNAL_URL: str = config("DGC_EXTERNAL_URL", default="")

BATCH_PERIODICITY_CRONTAB: str = config(
    "BATCH_PERIODICITY_CRONTAB",
    cast=validate_crontab("BATCH_PERIODICITY_CRONTAB"),
    default="0 0 * * *",
)

BATCH_EU_PERIODICITY_CRONTAB: str = config(
    "BATCH_EU_PERIODICITY_CRONTAB",
    cast=validate_crontab("BATCH_EU_PERIODICITY_CRONTAB"),
    default="0 0 * * *",
)

DELETE_OLD_DATA_CRONTAB: str = config(
    "DELETE_OLD_DATA_CRONTAB", cast=validate_crontab("DELETE_OLD_DATA_CRONTAB"), default="0 0 * * *"
)

MAX_PADDING_SIZE: int = config("MAX_PADDING_SIZE", cast=int, default=150_000)
