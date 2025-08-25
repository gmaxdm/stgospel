import pytz
import datetime


class TimezoneConverter:

    @staticmethod
    def from_to(dt, from_tz, to_tz):
        """
            dt: datetime in from_tz timezone to convert
            from_tz: from timezone
            to_tz: to timezone

            returns datetime in to_tz timezone
        """
        _from = pytz.timezone(from_tz)
        _to = pytz.timezone(to_tz)
        localized = _from.localize(dt)
        return localized.astimezone(_to)

