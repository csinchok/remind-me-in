import datetime
import pytz
import unittest

from remindmein.parse import parse_numbers, parse_morning


class ParsingTestCase(unittest.TestCase):

    def test_morning(self):
        created_at = datetime.datetime.now(pytz.utc)
        timezone = pytz.utc

        tomorrow = created_at + datetime.timedelta(days=1)

        for text in [' the morning', ' the am', ' the am.', ' the morning.', ' the a.m.']:
            when = parse_morning(text, created_at, timezone)
            assert when.day == tomorrow.day
            assert when.month == tomorrow.month
            assert when.year == tomorrow.year
            assert when.hour == 9
            assert when.minute == 30

    def test_numbers(self):
        created_at = datetime.datetime.now(pytz.utc)
        timezone = pytz.utc

        when = parse_numbers(' in 2 hours', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=2)

        when = parse_numbers(' in two hours', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=2)

        when = parse_numbers(' an hour', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=1)

        when = parse_numbers(' a couple hours', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=2)

        when = parse_numbers(' a couple of hours', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=2)

        when = parse_numbers(' a few hours', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(hours=3)

        when = parse_numbers(' fifteen minutes', created_at, timezone)
        assert (when - created_at) == datetime.timedelta(minutes=15)
