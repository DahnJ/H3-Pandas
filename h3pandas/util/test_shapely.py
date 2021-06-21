from shapely.geometry import Polygon, MultiPolygon, LineString
import pytest
from .shapely import polyfill


@pytest.fixture
def polygon():
    return Polygon([(48, 18), (49, 18), (49, 19), (48, 19)])


@pytest.fixture
def polygon_b():
    return Polygon([(54, 11), (56, 11), (56, 12), (54, 12)])


@pytest.fixture
def polygon_with_hole():
    return Polygon(
        [(48, 18), (49, 18), (49, 19), (48, 19)],
        [[(48.4, 18.2), (48.8, 18.2), (48.8, 18.6), (48.4, 18.6)]],
    )


@pytest.fixture
def multipolygon(polygon, polygon_b):
    return MultiPolygon([polygon, polygon_b])


@pytest.fixture
def line():
    return LineString([(0, 0), (1, 0), (1, 1)])


def test_polyfill_polygon(polygon):
    expected = set(["811e3ffffffffff"])
    result = polyfill(polygon, 1)
    assert expected == result


def test_polyfill_multipolygon(multipolygon):
    expected = set(["811e3ffffffffff", "811f3ffffffffff"])
    result = polyfill(multipolygon, 1)
    assert expected == result


def test_polyfill_polygon_with_hole(polygon_with_hole):
    expected = set()
    result = polyfill(polygon_with_hole, 1)
    assert expected == result


def test_polyfill_wrong_type(line):
    with pytest.raises(TypeError, match=".*Unknown type.*"):
        polyfill(line, 1)
