from . import h3pandas  # noqa: F401
from h3 import h3
import pytest
from shapely.geometry import Polygon, box
import pandas as pd
import geopandas as gpd

# TODO: Make sure methods are tested both for DataFrame and GeoDataFrame (where applicable)

# Fixtures

@pytest.fixture
def basic_dataframe():
    """DataFrame with lat and lng columns"""
    return pd.DataFrame({
        'lat': [50, 51],
        'lng': [14, 15]
    })


@pytest.fixture
def basic_geodataframe(basic_dataframe):
    """GeoDataFrame with POINT geometry"""
    geometry = gpd.points_from_xy(basic_dataframe['lng'], basic_dataframe['lat'])
    return gpd.GeoDataFrame(geometry=geometry, crs='epsg:4326')


@pytest.fixture
def basic_geodataframe_polygon(basic_geodataframe):
    geom = box(0, 0, 1, 1)
    return basic_geodataframe.assign(geometry=[geom, geom])


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
    return (basic_dataframe
            .assign(h3_09=['891e3097383ffff', '891e2659c2fffff'])
            .set_index('h3_09'))


@pytest.fixture
def h3_dataframe_with_values():
    """DataFrame with resolution 9 H3 index and values"""
    index = ['891f1d48177ffff', '891f1d48167ffff', '891f1d4810fffff']
    return pd.DataFrame({'val': [1, 2, 5]}, index=index)


@pytest.fixture
def h3_geodataframe_with_values(h3_dataframe_with_values):
    """GeoDataFrame with resolution 9 H3 index, values, and Hexagon geometries"""
    geometry = [Polygon(h3.h3_to_geo_boundary(h, True))
                for h in h3_dataframe_with_values.index]
    return gpd.GeoDataFrame(h3_dataframe_with_values, geometry=geometry,
                            crs='epsg:4326')


# Tests: H3 API

def test_geo_to_h3(basic_dataframe):
    result = basic_dataframe.h3.geo_to_h3(9)
    expected = (basic_dataframe
                .assign(h3_09=['891e3097383ffff', '891e2659c2fffff'])
                .set_index('h3_09'))

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_geo(basic_geodataframe):
    result = basic_geodataframe.h3.geo_to_h3(9)
    expected = (basic_geodataframe
                .assign(h3_09=['891e3097383ffff', '891e2659c2fffff'])
                .set_index('h3_09'))

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_polygon(basic_geodataframe_polygon):
    with pytest.raises(ValueError):
        basic_geodataframe_polygon.h3.geo_to_h3(9)


def test_h3_to_geo_boundary(indexed_dataframe):
    h1 = ((13.997875502962215, 50.00126530465277),
          (13.997981974191347, 49.99956539765703),
          (14.000478563108897, 49.99885162163456),
          (14.002868770645003, 49.99983773856239),
          (14.002762412857178, 50.00153765760209),
          (14.000265734090084, 50.00225144767143),
          (13.997875502962215, 50.00126530465277))
    h2 = ((14.9972390328545, 51.00084372147122),
          (14.99732334029277, 50.99916437137475),
          (14.999853173220332, 50.99844207137708),
          (15.002298787294139, 50.99939910547163),
          (15.002214597747209, 51.00107846572982),
          (14.999684676233445, 51.00180078173323),
          (14.9972390328545, 51.00084372147122))
    geometry = [Polygon(h1), Polygon(h2)]

    result = indexed_dataframe.h3.h3_to_geo_boundary()
    expected = gpd.GeoDataFrame(indexed_dataframe, geometry=geometry,
                                crs='epsg:4326')
    pd.testing.assert_frame_equal(expected, result)


def test_h3_to_geo_boundary_wrong_index(indexed_dataframe):
    indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ['invalid']
    with pytest.raises(ValueError):
        indexed_dataframe.h3.h3_to_geo_boundary()


def test_h3_to_parent(h3_dataframe_with_values):
    h3_parent = '811f3ffffffffff'
    result = h3_dataframe_with_values.h3.h3_to_parent(1)
    expected = h3_dataframe_with_values.assign(h3_01=h3_parent)

    pd.testing.assert_frame_equal(expected, result)


def test_h3_get_resolution(h3_dataframe_with_values):
    expected = h3_dataframe_with_values.assign(h3_resolution=9)
    result = h3_dataframe_with_values.h3.h3_get_resolution()
    pd.testing.assert_frame_equal(expected, result)


def test_h3_get_resolution_index_only(h3_dataframe_with_values):
    del h3_dataframe_with_values['val']
    expected = h3_dataframe_with_values.assign(h3_resolution=9)
    result = h3_dataframe_with_values.h3.h3_get_resolution()
    pd.testing.assert_frame_equal(expected, result)


# Tests: Aggregate functions


def test_geo_to_h3_aggregate(basic_dataframe_with_values):
    result = basic_dataframe_with_values.h3.geo_to_h3_aggregate(1)
    expected = (pd.DataFrame({'h3_01': ['811e3ffffffffff'], 'val': [2+5]})
                .set_index('h3_01'))

    pd.testing.assert_frame_equal(expected, result)


def test_geo_to_h3_aggregate_geo(basic_geodataframe_with_values):
    result = basic_geodataframe_with_values.h3.geo_to_h3_aggregate(1)
    expected = (pd.DataFrame({'h3_01': ['811e3ffffffffff'], 'val': [2+5]})
                .set_index('h3_01'))

    pd.testing.assert_frame_equal(expected, result)


def test_h3_to_parent_aggregate(h3_geodataframe_with_values):
    result = h3_geodataframe_with_values.h3.h3_to_parent_aggregate(8)
    # TODO: Why does Pandas not preserve the order of groups here?
    index = pd.Index(['881f1d4811fffff', '881f1d4817fffff'], name='h3_08')
    geometry = [Polygon(h3.h3_to_geo_boundary(h, True)) for h in index]
    expected = gpd.GeoDataFrame({'val': [5, 3]}, geometry=geometry,
                                index=index, crs='epsg:4326')

    pd.testing.assert_frame_equal(expected, result)


def test_h3_to_parent_aggregate_no_geometry(h3_dataframe_with_values):
    index = pd.Index(['881f1d4811fffff', '881f1d4817fffff'], name='h3_08')
    expected = pd.DataFrame({'val': [5, 3]}, index=index)
    result = h3_dataframe_with_values.h3.h3_to_parent_aggregate(8)
    pd.testing.assert_frame_equal(expected, result)
