from rsf import find_dateblock
import pytest
import io
from typing import Tuple, List


DocumentUsecase = Tuple[io.TextIOBase, List[str]]


@pytest.fixture
def ordinary_document():
    lines = (
        'First line',
        '',
        'rsf:',
        '- x 2022-03-10',
        '- 2022-03-15',
        '',
        'End of document.'
    )
    text = '\n'.join(lines)
    stream_ = io.StringIO(text)
    expected_dateblock = [
        '- x 2022-03-10',
        '- 2022-03-15',
    ]
    return stream_, expected_dateblock


@pytest.fixture
def abbreviated_nonideal_document():
    lines = (
        'rsf:   ',
        '-    x 2022-03-10  ',
        '- 2022-03-15   '
    )
    text = '\n'.join(lines)
    stream_ = io.StringIO(text)
    expected_dateblock = [
        '-    x 2022-03-10  ',
        '- 2022-03-15   '
    ]
    return stream_, expected_dateblock


def test_normal_usecase(
    ordinary_document: DocumentUsecase
):
    stream, expected = ordinary_document
    result = find_dateblock(stream=stream)
    assert result == expected


def test_abbreviated_nonideal_usecase(
    abbreviated_nonideal_document: DocumentUsecase
):
    stream, expected = abbreviated_nonideal_document
    result = find_dateblock(stream=stream)
    assert result == expected

