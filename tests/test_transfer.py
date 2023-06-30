import io

import pytest

from domino_data import transfer


@pytest.mark.parametrize(
    "start,end,step,expected",
    [
        (0, 10, 2, [(0, 1), (2, 3), (4, 5), (6, 7), (8, 10)]),
        (0, 10, 3, [(0, 2), (3, 5), (6, 8), (9, 10)]),
        (0, 10, 5, [(0, 4), (5, 10)]),
        (0, 10, 6, [(0, 5), (6, 10)]),
        (0, 10, 11, [(0, 10)]),
    ],
)
def test_split_range(start, end, step, expected):
    assert expected == list(transfer.split_range(start, end, step))


def test_blob_transfer():
    with io.BytesIO() as dest:
        transfer.BlobTransfer(
            "https://murat-secure-test.s3.us-west-2.amazonaws.com/9095835.png",
            dest,
            chunk_size=2**10,
        )

        assert 21821 == len(dest.getvalue())
