from rsf import _DATE_PATTERN, _END_PATTERN, _START_PATTERN


def test_DATE_PATTERN_regular_completed():

    text = '- x 2022-03-10'
    assert bool(_DATE_PATTERN.match(text)) is True


def test_DATE_PATTERN_regular_notcompleted():

    text = '- 2022-03-10'
    assert bool(_DATE_PATTERN.match(text)) is True


def test_DATE_PATTERN_irregular():

    text = '*X    2021-11-11    '
    assert bool(_DATE_PATTERN.match(text)) is True

    text_2 = '*  x2021-11-11    '
    assert bool(_DATE_PATTERN.match(text_2)) is True


def test_END_PATTERN_doesnt_match_dates():

    text = '- x 2022-03-10'
    result = bool(_END_PATTERN.match(text))
    assert result is False


def test_START_PATTERN_is_case_insensitive():

    text = 'rsf:'
    text_2 = 'RSF:'
    text_3 = 'rSf:'

    assert bool(_START_PATTERN.match(text)) is True
    assert bool(_START_PATTERN.match(text_2)) is True
    assert bool(_START_PATTERN.match(text_3)) is True

