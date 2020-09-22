from datetime import datetime, timedelta, timezone

_TEN_MINUTES_IN_SECONDS = timedelta(minutes=10).total_seconds()


def now_rolling_start_number() -> int:
    """
    Compute the rolling start number as of now.

    :return: the "now" rolling start number.
    """
    return _datetime_to_rolling_start_number(datetime.utcnow())


def today_midnight_rolling_start_number() -> int:
    """
    Compute the rolling start number as of today at midnight.

    :return: the rolling start number corresponding to today at midnight.
    """
    return _datetime_to_rolling_start_number(
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    )


def _datetime_to_rolling_start_number(_datetime: datetime) -> int:
    """
    Given a datetime, return the corresponding rolling start number.

    :param _datetime: the datetime whose rolling start is to be calculated.

    :return: the rolling start corresponding to the given datetime.
    """
    return int(_datetime.replace(tzinfo=timezone.utc).timestamp() / _TEN_MINUTES_IN_SECONDS)
