from rsf import DueDate

import pytest
from typing import Tuple
from datetime import date


@pytest.fixture
def date_triplet():
    a = date(2022, 3, 10)
    b = date(2022, 3, 12)
    c = date(2022, 3, 15)
    return a, b, c


def test_can_be_sorted(date_triplet: Tuple[date, date, date]):
    
    date_a, date_b, date_c = date_triplet
    due_a, due_b, due_c = (
        DueDate(date=date_a, completed=True),
        DueDate(date=date_b, completed=True),
        DueDate(date=date_c, completed=True)
    )
    correct_order = [due_a, due_b, due_c]
    reversed_order = [due_c, due_b, due_a]

    result_corrected_order = sorted(reversed_order)
    assert result_corrected_order == correct_order


def test_from_datestr_completed():
    datestr = '- x 2022-07-18'
    result = DueDate.from_datestr(datestr)
    assert result.completed is True


def test_from_datestr_notcompleted():
    datestr = '- 2022-07-18'
    result = DueDate.from_datestr(datestr)
    assert result.completed is False

