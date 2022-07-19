from rsf import DateRange
from datetime import date 
import pytest


@pytest.fixture
def earliest():
    return date(2022, 3, 10)


@pytest.fixture
def latest():
    return date(2022, 3, 15)


@pytest.fixture
def daterange(earliest: date, latest: date):
    return DateRange(
        earliest=earliest,
        latest=latest
    )


def test_method_in_range_on_earliest(daterange: DateRange, earliest: date):
    assert earliest in daterange


def test_method_in_range_on_latest(daterange: DateRange, latest: date):
    assert latest in daterange


def test_method_in_range_in_middle(daterange: DateRange):
    test_date = date(2022, 3, 12)
    assert test_date in daterange

