import operator
from typing import List

from marshmallow import ValidationError
from marshmallow.validate import Validator

from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from immuni_exposure_ingestion.core import config


class TekListValidator(Validator):
    """
    A validator for a list of TEKs.
    """

    def __call__(self, value: List[TemporaryExposureKey]) -> None:
        """
        Validations to be performed according to Apple's documentation:

        - Any ENIntervalNumber values from the same user are not unique.
        - The period of time covered by the data file exceeds 14 days.
        - Any keys in the file have overlapping time windows.
        - The TEKRollingPeriod value is not 144.

        :param value: the value of the schema being validated.
        """

        if len(value) == 0:
            return

        # NOTE: This kind of validation (rolling_period == 144) could be performed at field level.
        #   We expect all of these validations to change in the future, so having them all together
        #   here is done on purpose to make things simpler in case of changes in validation.
        #   We would like to keep field validation more flexible as not to spread strict validation
        #   logic in many places.

        if any(tek.rolling_period != 144 for tek in value):
            raise ValidationError("Some rolling values are not 144.")

        if (n_keys := len(value)) > config.MAX_KEYS_PER_UPLOAD:
            raise ValidationError(
                f"Too many TEKs. (actual: {n_keys}, max_allowed: {config.MAX_KEYS_PER_UPLOAD})"
            )

        sorted_teks = sorted(value, key=operator.attrgetter("rolling_start_number"))
        rolling_start_numbers = [t.rolling_start_number for t in sorted_teks]

        if len(rolling_start_numbers) != len(set(rolling_start_numbers)):
            raise ValidationError("Rolling start numbers are not unique")

        next_rolling_start_number = sorted_teks[0].rolling_start_number
        for current in sorted_teks:
            if current.rolling_start_number < next_rolling_start_number:
                raise ValidationError("Overlapping rolling start numbers")
            next_rolling_start_number = current.rolling_start_number + current.rolling_period
