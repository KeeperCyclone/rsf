from rsf import _droptake as droptake


def lt_10(x) -> bool:
    return x < 10


def gt_10(x) -> bool:
    return x > 10


def test_droptake():

    seq = (1, 2, 3, 11, 23, 45, 1, 2, 3)
    
    expected = (23, 45)
    result = tuple(
        droptake(
            drop_pred=lt_10,
            take_pred=gt_10,
            iterable=seq
        )
    )
    assert result == expected