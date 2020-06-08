from typing import List

from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey
from marshmallow import ValidationError
from marshmallow.validate import Validator


class TekListValidator(Validator):
    """
    A validator for a list of TEKs.
    """

    def __call__(self, value: List[TemporaryExposureKey]) -> None:
        """
        Validations to be performed according to Apple's documentation:

        - Any ENIntervalNumber values from the same user are not unique.
        - The period of time covered by the data file exceeds 14 days.
        - There are any gaps in the ENIntervalNumber values for a user.
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

        if (n_keys := len(value)) > 14:
            raise ValidationError(f"Too many TEKs. (actual: {n_keys}, max_allowed: 14)")

        rolling_start_numbers = set(tek.rolling_start_number for tek in value)
        min_start_number = min(rolling_start_numbers)
        expected_start_numbers = set(min_start_number + 144 * i for i in range(n_keys))

        if rolling_start_numbers != expected_start_numbers:
            raise ValidationError("Unexpected rolling start numbers identified.")
