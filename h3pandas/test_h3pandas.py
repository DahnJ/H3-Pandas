from . import h3pandas  # noqa: F401
from h3 import h3
import pytest
from shapely.geometry import Polygon, box
import pandas as pd
import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal


# TODO: Make sure methods are tested both for
#  DataFrame and GeoDataFrame (where applicable)
# TODO: Test return_geometry functionality

# Fixtures


@pytest.fixture
def basic_dataframe():
    """DataFrame with lat and lng columns"""
    return pd.DataFrame({"lat": [50, 51], "lng": [14, 15]})


@pytest.fixture
def basic_geodataframe(basic_dataframe):
    """GeoDataFrame with POINT geometry"""
    geometry = gpd.points_from_xy(basic_dataframe["lng"], basic_dataframe["lat"])
    return gpd.GeoDataFrame(geometry=geometry, crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_polygon(basic_geodataframe):
    geom = box(0, 0, 1, 1)
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_polygons(basic_geodataframe):
    geoms = [box(0, 0, 1, 1), box(0, 0, 2, 2)]
    return gpd.GeoDataFrame(geometry=geoms, crs="epsg:4326")


@pytest.fixture
def basic_dataframe_with_values(basic_dataframe):
    """DataFrame with lat and lng columns and values"""
    return basic_dataframe.assign(val=[2, 5])


@pytest.fixture
def basic_geodataframe_with_values(basic_geodataframe):
    """GeoDataFrame with POINT geometry and values"""
    return basic_geodataframe.assign(val=[2, 5])


@pytest.fixture
def indexed_dataframe(basic_dataframe):
    """DataFrame with lat, lng and resolution 9 H3 index"""
    return basic_dataframe.assign(
        h3_09=["891e3097383ffff", "891e2659c2fffff"]
    ).set_index("h3_09")


@pytest.fixture
def h3_dataframe_with_values():
    """DataFrame with resolution 9 H3 index and values"""
    index = ["891f1d48177ffff", "891f1d48167ffff", "891f1d4810fffff"]
    return pd.DataFrame({"val": [1, 2, 5]}, index=index)


@pytest.fixture
def h3_geodataframe_with_values(h3_dataframe_with_values):
    """GeoDataFrame with resolution 9 H3 index, values, and Hexagon geometries"""
    geometry = [
        Polygon(h3.h3_to_geo_boundary(h, True)) for h in h3_dataframe_with_values.index
    ]
    return gpd.GeoDataFrame(
        h3_dataframe_with_values, geometry=geometry, crs="epsg:4326"
    )


# Tests: H3 API


def test_geo_to_h3(basic_dataframe):
    result = basic_dataframe.h3.geo_to_h3(9)
    expected = basic_dataframe.assign(
        h3_09=["891e3097383ffff", "891e2659c2fffff"]
    ).set_index("h3_09")

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_geo(basic_geodataframe):
    result = basic_geodataframe.h3.geo_to_h3(9)
    expected = basic_geodataframe.assign(
        h3_09=["891e3097383ffff", "891e2659c2fffff"]
    ).set_index("h3_09")

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_polygon(basic_geodataframe_polygon):
    with pytest.raises(ValueError):
        basic_geodataframe_polygon.h3.geo_to_h3(9)


def test_h3_to_geo(indexed_dataframe):
    lats = [50.000551554902586, 51.000121447274736]
    lngs = [14.000372151097624, 14.999768926738376]
    geometry = gpd.points_from_xy(x=lngs, y=lats, crs="epsg:4326")
    expected = gpd.GeoDataFrame(indexed_dataframe, geometry=geometry)
    result = indexed_dataframe.h3.h3_to_geo()
    assert_geodataframe_equal(expected, result, check_less_precise=True)


def test_h3_to_geo_boundary(indexed_dataframe):
    h1 = (
        (13.997875502962215, 50.00126530465277),
        (13.997981974191347, 49.99956539765703),
        (14.000478563108897, 49.99885162163456),
        (14.002868770645003, 49.99983773856239),
        (14.002762412857178, 50.00153765760209),
        (14.000265734090084, 50.00225144767143),
        (13.997875502962215, 50.00126530465277),
    )
    h2 = (
        (14.9972390328545, 51.00084372147122),
        (14.99732334029277, 50.99916437137475),
        (14.999853173220332, 50.99844207137708),
        (15.002298787294139, 50.99939910547163),
        (15.002214597747209, 51.00107846572982),
        (14.999684676233445, 51.00180078173323),
        (14.9972390328545, 51.00084372147122),
    )
    geometry = [Polygon(h1), Polygon(h2)]

    result = indexed_dataframe.h3.h3_to_geo_boundary()
    expected = gpd.GeoDataFrame(indexed_dataframe, geometry=geometry, crs="epsg:4326")
    assert_geodataframe_equal(expected, result, check_less_precise=True)


def test_h3_to_geo_boundary_wrong_index(indexed_dataframe):
    indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ["invalid"]
    with pytest.raises(ValueError):
        indexed_dataframe.h3.h3_to_geo_boundary()


def test_h3_to_parent(h3_dataframe_with_values):
    h3_parent = "811f3ffffffffff"
    result = h3_dataframe_with_values.h3.h3_to_parent(1)
    expected = h3_dataframe_with_values.assign(h3_01=h3_parent)

    pd.testing.assert_frame_equal(expected, result)


def test_h3_to_center_child(indexed_dataframe):
    expected = indexed_dataframe.assign(
        h3_center_child=["8a1e30973807fff", "8a1e2659c2c7fff"]
    )
    result = indexed_dataframe.h3.h3_to_center_child()
    pd.testing.assert_frame_equal(expected, result)


def test_empty_polyfill(h3_geodataframe_with_values):
    expected = h3_geodataframe_with_values.assign(h3_polyfill=[list(), list(), list()])
    result = h3_geodataframe_with_values.h3.polyfill(1)
    assert_geodataframe_equal(expected, result)


def test_polyfill(h3_geodataframe_with_values):
    expected_cells = [
        {
            "8a1f1d481747fff",
            "8a1f1d48174ffff",
            "8a1f1d481757fff",
            "8a1f1d48175ffff",
            "8a1f1d481767fff",
            "8a1f1d48176ffff",
            "8a1f1d481777fff",
        },
        {
            "8a1f1d481647fff",
            "8a1f1d48164ffff",
            "8a1f1d481657fff",
            "8a1f1d48165ffff",
            "8a1f1d481667fff",
            "8a1f1d48166ffff",
            "8a1f1d481677fff",
        },
        {
            "8a1f1d4810c7fff",
            "8a1f1d4810cffff",
            "8a1f1d4810d7fff",
            "8a1f1d4810dffff",
            "8a1f1d4810e7fff",
            "8a1f1d4810effff",
            "8a1f1d4810f7fff",
        },
    ]
    expected = h3_geodataframe_with_values.assign(h3_polyfill=expected_cells)
    result = h3_geodataframe_with_values.h3.polyfill(10)
    result["h3_polyfill"] = result["h3_polyfill"].apply(
        set
    )  # Convert to set for testing
    assert_geodataframe_equal(expected, result)


def test_polyfill_explode(h3_geodataframe_with_values):
    expected_indices = set().union(
        *[
            {
                "8a1f1d481747fff",
                "8a1f1d48174ffff",
                "8a1f1d481757fff",
                "8a1f1d48175ffff",
                "8a1f1d481767fff",
                "8a1f1d48176ffff",
                "8a1f1d481777fff",
            },
            {
                "8a1f1d481647fff",
                "8a1f1d48164ffff",
                "8a1f1d481657fff",
                "8a1f1d48165ffff",
                "8a1f1d481667fff",
                "8a1f1d48166ffff",
                "8a1f1d481677fff",
            },
            {
                "8a1f1d4810c7fff",
                "8a1f1d4810cffff",
                "8a1f1d4810d7fff",
                "8a1f1d4810dffff",
                "8a1f1d4810e7fff",
                "8a1f1d4810effff",
                "8a1f1d4810f7fff",
            },
        ]
    )
    result = h3_geodataframe_with_values.h3.polyfill(10, explode=True)
    assert len(result) == len(h3_geodataframe_with_values) * 7
    assert set(result["h3_polyfill"]) == expected_indices
    assert not result["val"].isna().any()


def test_polyfill_explode_unequal_lengths(basic_geodataframe_polygons):
    expected_indices = {
        "83754efffffffff",
        "83756afffffffff",
        "83754efffffffff",
        "837541fffffffff",
        "83754cfffffffff",
    }
    result = basic_geodataframe_polygons.h3.polyfill(3, explode=True)
    assert len(result) == 5
    assert set(result["h3_polyfill"]) == expected_indices


def test_cell_area(indexed_dataframe):
    expected = indexed_dataframe.assign(
        h3_cell_area=[0.09937867173389912, 0.09775508251476996]
    )
    result = indexed_dataframe.h3.cell_area()
    pd.testing.assert_frame_equal(expected, result)


def test_h3_get_resolution(h3_dataframe_with_values):
    expected = h3_dataframe_with_values.assign(h3_resolution=9)
    result = h3_dataframe_with_values.h3.h3_get_resolution()
    pd.testing.assert_frame_equal(expected, result)


def test_h3_get_base_cell(indexed_dataframe):
    expected = indexed_dataframe.assign(h3_base_cell=[15, 15])
    result = indexed_dataframe.h3.h3_get_base_cell()
    pd.testing.assert_frame_equal(expected, result)


def test_h3_0_ring(indexed_dataframe):
    expected = indexed_dataframe.assign(
        h3_k_ring=[[h] for h in indexed_dataframe.index]
    )
    result = indexed_dataframe.h3.k_ring(0)
    pd.testing.assert_frame_equal(expected, result)


def test_h3_k_ring(indexed_dataframe):
    expected_indices = [
        {
            "891e3097383ffff",
            "891e3097387ffff",
            "891e309738bffff",
            "891e309738fffff",
            "891e3097393ffff",
            "891e3097397ffff",
            "891e309739bffff",
        },
        {
            "891e2659893ffff",
            "891e2659897ffff",
            "891e2659c23ffff",
            "891e2659c27ffff",
            "891e2659c2bffff",
            "891e2659c2fffff",
            "891e2659d5bffff",
        },
    ]
    expected = indexed_dataframe.assign(h3_k_ring=expected_indices)
    result = indexed_dataframe.h3.k_ring()
    result["h3_k_ring"] = result["h3_k_ring"].apply(set)  # Convert to set for testing
    pd.testing.assert_frame_equal(expected, result)


def test_h3_k_ring_explode(indexed_dataframe):
    expected_indices = set().union(
        *[
            {
                "891e3097383ffff",
                "891e3097387ffff",
                "891e309738bffff",
                "891e309738fffff",
                "891e3097393ffff",
                "891e3097397ffff",
                "891e309739bffff",
            },
            {
                "891e2659893ffff",
                "891e2659897ffff",
                "891e2659c23ffff",
                "891e2659c27ffff",
                "891e2659c2bffff",
                "891e2659c2fffff",
                "891e2659d5bffff",
            },
        ]
    )
    result = indexed_dataframe.h3.k_ring(explode=True)
    assert len(result) == len(indexed_dataframe) * 7
    assert set(result["h3_k_ring"]) == expected_indices
    assert not result["lat"].isna().any()


def test_h3_0_hex_ring(indexed_dataframe):
    expected = indexed_dataframe.assign(
        h3_hex_ring=[[h] for h in indexed_dataframe.index]
    )
    result = indexed_dataframe.h3.hex_ring(0)
    pd.testing.assert_frame_equal(expected, result)


def test_h3_0_hex_ring_explode(indexed_dataframe):
    expected = indexed_dataframe.assign(
        h3_hex_ring=[h for h in indexed_dataframe.index]
    )
    result = indexed_dataframe.h3.hex_ring(0, True)
    pd.testing.assert_frame_equal(expected, result)


def test_h3_hex_ring(indexed_dataframe):
    expected_indices = [
        {
            "891e3097387ffff",
            "891e309738bffff",
            "891e309738fffff",
            "891e3097393ffff",
            "891e3097397ffff",
            "891e309739bffff",
        },
        {
            "891e2659893ffff",
            "891e2659897ffff",
            "891e2659c23ffff",
            "891e2659c27ffff",
            "891e2659c2bffff",
            "891e2659d5bffff",
        },
    ]
    expected = indexed_dataframe.assign(h3_hex_ring=expected_indices)
    result = indexed_dataframe.h3.hex_ring()
    result["h3_hex_ring"] = result["h3_hex_ring"].apply(
        set
    )  # Convert to set for testing
    pd.testing.assert_frame_equal(expected, result)


def test_h3_hex_ring_explode(indexed_dataframe):
    expected_indices = set().union(
        *[
            {
                "891e3097387ffff",
                "891e309738bffff",
                "891e309738fffff",
                "891e3097393ffff",
                "891e3097397ffff",
                "891e309739bffff",
            },
            {
                "891e2659893ffff",
                "891e2659897ffff",
                "891e2659c23ffff",
                "891e2659c27ffff",
                "891e2659c2bffff",
                "891e2659d5bffff",
            },
        ]
    )
    result = indexed_dataframe.h3.hex_ring(explode=True)
    assert len(result) == len(indexed_dataframe) * 6
    assert set(result["h3_hex_ring"]) == expected_indices
    assert not result["lat"].isna().any()


def test_h3_is_valid(indexed_dataframe):
    indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ["invalid"]
    expected = indexed_dataframe.assign(h3_is_valid=[True, False])
    result = indexed_dataframe.h3.h3_is_valid()
    pd.testing.assert_frame_equal(expected, result)


def test_h3_get_resolution_index_only(h3_dataframe_with_values):
    del h3_dataframe_with_values["val"]
    expected = h3_dataframe_with_values.assign(h3_resolution=9)
    result = h3_dataframe_with_values.h3.h3_get_resolution()
    pd.testing.assert_frame_equal(expected, result)


# Tests: Aggregate functions


def test_geo_to_h3_aggregate(basic_dataframe_with_values):
    result = basic_dataframe_with_values.h3.geo_to_h3_aggregate(
        1, return_geometry=False
    )
    expected = pd.DataFrame({"h3_01": ["811e3ffffffffff"], "val": [2 + 5]}).set_index(
        "h3_01"
    )

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_aggregate_geo(basic_geodataframe_with_values):
    result = basic_geodataframe_with_values.h3.geo_to_h3_aggregate(
        1, return_geometry=False
    )
    expected = pd.DataFrame({"h3_01": ["811e3ffffffffff"], "val": [2 + 5]}).set_index(
        "h3_01"
    )

    pd.testing.assert_frame_equal(expected, result)


def test_h3_to_parent_aggregate(h3_geodataframe_with_values):
    result = h3_geodataframe_with_values.h3.h3_to_parent_aggregate(8)
    # TODO: Why does Pandas not preserve the order of groups here?
    index = pd.Index(["881f1d4811fffff", "881f1d4817fffff"], name="h3_08")
    geometry = [Polygon(h3.h3_to_geo_boundary(h, True)) for h in index]
    expected = gpd.GeoDataFrame(
        {"val": [5, 3]}, geometry=geometry, index=index, crs="epsg:4326"
    )

    assert_geodataframe_equal(expected, result)


def test_h3_to_parent_aggregate_no_geometry(h3_dataframe_with_values):
    index = pd.Index(["881f1d4811fffff", "881f1d4817fffff"], name="h3_08")
    expected = pd.DataFrame({"val": [5, 3]}, index=index)
    result = h3_dataframe_with_values.h3.h3_to_parent_aggregate(
        8, return_geometry=False
    )
    pd.testing.assert_frame_equal(expected, result)


def test_h3_k_ring_smoothing_k_vs_weighting(h3_dataframe_with_values):
    result_k = h3_dataframe_with_values.h3.k_ring_smoothing(2)
    result_weighted = h3_dataframe_with_values.h3.k_ring_smoothing(weights=[1, 1, 1])
    pd.testing.assert_frame_equal(result_k, result_weighted)


def test_h3_k_ring_smoothing_0_ring(h3_dataframe_with_values):
    expected = h3_dataframe_with_values.copy().sort_index().astype({"val": float})
    expected.index = expected.index.rename("h3_k_ring")
    result = h3_dataframe_with_values.h3.k_ring_smoothing(0, return_geometry=False)
    pd.testing.assert_frame_equal(expected, result)


def test_h3_k_ring_smoothing_0_ring_weights(h3_dataframe_with_values):
    expected = h3_dataframe_with_values.copy().sort_index().astype({"val": float})
    expected.index = expected.index.rename("h3_k_ring")
    result = h3_dataframe_with_values.h3.k_ring_smoothing(
        weights=[1], return_geometry=False
    )
    pd.testing.assert_frame_equal(expected, result)


def test_h3_k_ring_smoothing_2_ring(h3_dataframe_with_values):
    data = h3_dataframe_with_values.iloc[:1]
    expected = set([1 / 19])
    result = set(data.h3.k_ring_smoothing(2)["val"])
    assert expected == result


def test_h3_k_ring_smoothing_1_ring_weighted(h3_dataframe_with_values):
    data = h3_dataframe_with_values.iloc[:1]
    expected = set([1 / 4, 1 / 8])
    result = set(data.h3.k_ring_smoothing(weights=[2, 1])["val"])
    assert expected == result


def test_polyfill_resample(h3_geodataframe_with_values):
    expected_indices = set().union(
        *[
            {
                "8a1f1d481747fff",
                "8a1f1d48174ffff",
                "8a1f1d481757fff",
                "8a1f1d48175ffff",
                "8a1f1d481767fff",
                "8a1f1d48176ffff",
                "8a1f1d481777fff",
            },
            {
                "8a1f1d481647fff",
                "8a1f1d48164ffff",
                "8a1f1d481657fff",
                "8a1f1d48165ffff",
                "8a1f1d481667fff",
                "8a1f1d48166ffff",
                "8a1f1d481677fff",
            },
            {
                "8a1f1d4810c7fff",
                "8a1f1d4810cffff",
                "8a1f1d4810d7fff",
                "8a1f1d4810dffff",
                "8a1f1d4810e7fff",
                "8a1f1d4810effff",
                "8a1f1d4810f7fff",
            },
        ]
    )
    expected_values = set([1, 2, 5])
    result = h3_geodataframe_with_values.h3.polyfill_resample(10, return_geometry=False)
    assert len(result) == len(h3_geodataframe_with_values) * 7
    assert set(result.index) == expected_indices
    assert set(result["val"]) == expected_values
    assert not result["val"].isna().any()


def test_polyfill_resample_uncovered_rows(basic_geodataframe_polygons):
    basic_geodataframe_polygons.loc[2] = box(0, 0, 3, 3)
    with pytest.warns(UserWarning):
        result = basic_geodataframe_polygons.h3.polyfill_resample(2)

    assert len(result) == 2
