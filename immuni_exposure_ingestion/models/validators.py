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
import operator
from typing import List

from marshmallow import ValidationError
from marshmallow.validate import Validator

from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config
from immuni_exposure_ingestion.helpers.temporary_exposure_key import (
    now_rolling_start_number,
    today_midnight_rolling_start_number,
)

_LOGGER = logging.getLogger(__name__)

_ROLLING_PERIOD_MIN = 1
_ROLLING_PERIOD_MAX = 144


class TekListValidator(Validator):
    """
    A validator for a list of TEKs.
    """

    def __call__(self, teks: List[TemporaryExposureKey]) -> List[TemporaryExposureKey]:
        """
        Perform the validation of a given list of TEKs, both on punctual value and as a whole.

        NOTE: The validation of a single TEKs could be performed at field level.
          We expect (some of) these validations to change in the future. Having them all together
          here aims at easing any future change in the validation steps.

        :param teks: the list of TEKs to be validated.

        :raises ValidationError: in case at least one TEK is deemed invalid.
        :return: the list of valid TEKs.
        """

        n_teks = len(teks)
        _LOGGER.info("Validating TEKs.", extra=dict(n_teks=n_teks))

        if n_teks == 0:
            return []

        self._validate_aggregate_values(teks=teks)
        self._validate_single_values(teks=teks)

        return teks

    @staticmethod
    def _validate_aggregate_values(teks: List[TemporaryExposureKey]) -> None:
        """
        Validate the given TEKs, at an aggregate level.
        Raise as soon as an invalid TEK is found.

        :param teks: the list of TEKs to be validated.
        :raises: ValidationError in case at least one TEK is deemed invalid.
        """
        n_teks = len(teks)
        if n_teks > config.MAX_KEYS_PER_UPLOAD:
            raise ValidationError(
                f"Too many TEKs. (actual: {n_teks}, max_allowed: {config.MAX_KEYS_PER_UPLOAD})."
            )

        if len({tek.key_data for tek in teks}) != n_teks:
            raise ValidationError("TEKs do not have unique key data.")

        if len({(tek.rolling_start_number, tek.rolling_period) for tek in teks}) != n_teks:
            raise ValidationError("TEKs do not have unique (rolling_start_number, rolling_period).")

        unique_rolling_start_numbers = {
            tek.rolling_start_number
            for tek in sorted(teks, key=operator.attrgetter("rolling_start_number"))
        }

        initial_start_number = min(unique_rolling_start_numbers)

        if invalid_start_numbers := [
            tek.rolling_start_number
            for tek in teks
            if (tek.rolling_start_number - initial_start_number) % _ROLLING_PERIOD_MAX != 0
        ]:
            raise ValidationError(
                f"There are invalid rolling_start_number values "
                f"(i.e., {','.join(str(number) for number in invalid_start_numbers)})."
            )

        if not config.ALLOW_NON_CONSECUTIVE_TEKS:
            missing_rolling_start_numbers = {
                initial_start_number + _ROLLING_PERIOD_MAX * i
                for i in range(len(unique_rolling_start_numbers))
            }.difference(unique_rolling_start_numbers)
            if missing_rolling_start_numbers:
                raise ValidationError(
                    f"Some rolling_start_numbers are missing "
                    f"(i.e., {','.join(str(number) for number in missing_rolling_start_numbers)})."
                )

    @staticmethod
    def _validate_single_values(teks: List[TemporaryExposureKey]) -> None:
        """
        Validate the given TEKs, at single-TEK level.
        Raise as soon as an invalid TEK is found.

        :param teks: the list of TEKs to be validated.
        :raises: ValidationError in case at least one TEK is deemed invalid.
        """

        valid_teks = list()
        today_teks = list()
        _now_rolling_start_number = now_rolling_start_number()
        _today_midnight_rolling_start_number = today_midnight_rolling_start_number()

        for tek in teks:

            if _ROLLING_PERIOD_MIN <= tek.rolling_period <= _ROLLING_PERIOD_MAX:
                valid_teks.append(tek)
            else:
                # The TEK is not coming from the exposure notification framework: immediate short
                # circuit.
                raise ValidationError(
                    f"Some rolling_period values are not in "
                    f"[{_ROLLING_PERIOD_MIN},{_ROLLING_PERIOD_MAX}] (e.g., {tek.rolling_period})."
                )

            if (
                _today_midnight_rolling_start_number
                <= tek.rolling_start_number
                < _now_rolling_start_number
            ):
                today_teks.append(tek)
            elif tek.rolling_start_number >= _now_rolling_start_number:
                # The TEK is not coming from the exposure notification framework: immediate short
                # circuit.
                raise ValidationError(
                    f"Some rolling_start_number values are in the future "
                    f"(e.g., {tek.rolling_start_number})."
                )

        if today_teks:
            _LOGGER.info(
                "There are today's TEKs. "
                "They could be later ignored based on a configuration variable.",
                extra=dict(
                    n_teks=len(teks),
                    n_valid_teks=len(valid_teks),
                    n_today_teks=len(today_teks),
                    today_rolling_periods=list(tek.rolling_period for tek in today_teks),
                    EXCLUDE_CURRENT_DAY_TEK=config.EXCLUDE_CURRENT_DAY_TEK,
                ),
            )
