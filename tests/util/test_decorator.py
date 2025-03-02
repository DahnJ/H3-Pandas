import h3
import pytest

from h3pandas.util.decorator import catch_invalid_h3_address, sequential_deduplication


class TestCatchInvalidH3Address:
    def test_catch_invalid_h3_address(self):
        @catch_invalid_h3_address
        def safe_h3_to_parent(h3_address):
            return h3.cell_to_parent(h3_address, 1)

        with pytest.raises(ValueError):
            safe_h3_to_parent("a")  # Originally ValueError

        with pytest.raises(ValueError):
            safe_h3_to_parent(1)  # Originally TypeError

        with pytest.raises(ValueError):
            safe_h3_to_parent("891f1d48177fff1")  # Originally H3CellError


class TestSequentialDeduplication:
    def test_catch_sequential_duplicate_h3_addresses(self):
        @sequential_deduplication
        def function_taking_iterator(iterator):
            yield from iterator

        _input = [1, 1, 2, 3, 3, 4, 5, 4, 3, 3, 2, 1, 1]
        result = function_taking_iterator(_input)
        assert list(result) == [1, 2, 3, 4, 5, 4, 3, 2, 1]
