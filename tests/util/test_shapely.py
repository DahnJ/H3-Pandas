from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
import pytest
from h3pandas.util.shapely import polyfill, linetrace


@pytest.fixture
def polygon():
    return Polygon([(18, 48), (18, 49), (19, 49), (19, 48)])


@pytest.fixture
def polygon_b():
    return Polygon([(11, 54), (11, 56), (12, 56), (12, 54)])


@pytest.fixture
def polygon_with_hole():
    return Polygon(
        [(18, 48), (19, 48), (19, 49), (18, 49)],
        [[(18.2, 48.4), (18.6, 48.4), (18.6, 48.8), (18.2, 48.8)]],
    )


@pytest.fixture
def multipolygon(polygon, polygon_b):
    return MultiPolygon([polygon, polygon_b])


@pytest.fixture
def line():
    return LineString([(0, 0), (1, 0), (1, 1)])


@pytest.fixture
def multiline():
    return MultiLineString([[(0, 0), (1, 0), (1, 1)], [(1, 1), (0, 1), (0, 0)]])


class TestPolyfill:
    def test_polyfill_polygon(self, polygon):
        expected = set(["811e3ffffffffff"])
        result = polyfill(polygon, 1)
        assert expected == result

    def test_polyfill_multipolygon(self, multipolygon):
        expected = set(["811e3ffffffffff", "811f3ffffffffff"])
        result = polyfill(multipolygon, 1)
        assert expected == result

    def test_polyfill_polygon_with_hole(self, polygon_with_hole):
        expected = set()
        result = polyfill(polygon_with_hole, 1)
        assert expected == result

    def test_polyfill_wrong_type(self, line):
        with pytest.raises(TypeError, match=".*Unknown type.*"):
            polyfill(line, 1)


class TestLineTrace:
    def test_linetrace_linestring(self, line):
        expected = ["81757ffffffffff"]
        result = list(linetrace(line, 1))
        assert expected == result

        expected2 = ["82754ffffffffff", "827547fffffffff"]
        result2 = list(linetrace(line, 2))
        assert expected2 == result2

    def test_linetrace_multilinestring(self, multiline):
        expected = ["81757ffffffffff"]
        result = list(linetrace(multiline, 1))
        assert expected == result

        # Lists not sets, repeated items are expected, just not in sequence
        expected2 = ["82754ffffffffff", "827547fffffffff", "82754ffffffffff"]
        result2 = list(linetrace(multiline, 2))
        assert expected2 == result2
