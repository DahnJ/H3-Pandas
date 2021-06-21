from h3 import h3
import pytest

from .decorator import catch_invalid_h3_address


def test_catch_invalid_h3_address():
    @catch_invalid_h3_address
    def safe_h3_to_parent(h3_address):
        return h3.h3_to_parent(h3_address, 1)

    with pytest.raises(ValueError):
        safe_h3_to_parent("a")  # Originally ValueError

    with pytest.raises(ValueError):
        safe_h3_to_parent(1)  # Originally TypeError

    with pytest.raises(ValueError):
        safe_h3_to_parent("891f1d48177fff1")  # Originally H3CellError
