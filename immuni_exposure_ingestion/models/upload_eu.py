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
from datetime import datetime
from typing import List

from bson import ObjectId
from mongoengine import BooleanField, DateField, Document, EmbeddedDocumentListField, StringField
from pymongo.cursor import Cursor

from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey

_LOGGER = logging.getLogger(__name__)


class UploadEu(Document):
    """
    Model of an Upload from the efgs gateway.
    """

    to_publish = BooleanField(default=True)
    keys = EmbeddedDocumentListField(TemporaryExposureKey, required=False, default=[])
    symptoms_started_on = DateField(required=True)
    country = StringField(required=True)

    meta = {"indexes": ["to_publish"]}

    @classmethod
    def countries_to_process(cls) -> Cursor:
        """
        Fetch all countries yet to be processed.

        :return: the cursor that iterates over distinct countries that are yet to be processed.
        """
        return cls.objects.filter(to_publish=True).distinct(field="country")

    @classmethod
    def to_process(cls, country_: str) -> Cursor:
        """
        Fetch all of the Uploads by country yet to be processed.

        :return: the cursor that iterates over Uploads by country that are yet to be processed.
        """
        return cls.objects.filter(to_publish=True, country=country_).order_by("id")

    @classmethod
    def unprocessed_before(cls, datetime_: datetime) -> bool:
        """
        Assess whether there are unprocessed Uploads older than the specified datetime.

        :param datetime_: the datetime to check against.
        :return: True if there are unprocessed Uploads older than the specified datetime, False
          otherwise.
        """
        return (
                cls.objects.filter(id__lte=ObjectId.from_datetime(datetime_), to_publish=True).count()
                > 0
        )

    @classmethod
    def set_published(cls, ids: List[ObjectId]) -> None:
        """
        Mark the Uploads corresponding to the given ids as published.

        :param ids: the list of ids of the Uploads to mark as published.
        """
        cls.objects(id__in=ids).update(to_publish=False)

    @classmethod
    def delete_older_than(cls, datetime_: datetime) -> int:
        """
        Delete all Uploads older than the given datetime.

        :param datetime_: the datetime to check against.
        :return: the number of deleted documents.
        """
        return cls.objects.filter(id__lte=ObjectId.from_datetime(datetime_)).delete()
