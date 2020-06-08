from immuni_exposure_ingestion.models.validators import TekListValidator


def test_tek_key_validator_pass_if_empty() -> None:
    TekListValidator().__call__([])
