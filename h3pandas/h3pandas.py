from typing import Union, Callable, Sequence, Any
import warnings

# Literal is not supported by Python <3.8
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import numpy as np
import shapely
import pandas as pd
import geopandas as gpd

from h3 import h3
from pandas.core.frame import DataFrame
from geopandas.geodataframe import GeoDataFrame

from .const import COLUMN_H3_POLYFILL
from .util.decorator import catch_invalid_h3_address, doc_standard
from .util.functools import wrapped_partial
from .util.shapely import polyfill

AnyDataFrame = Union[DataFrame, GeoDataFrame]


@pd.api.extensions.register_dataframe_accessor("h3")
class H3Accessor:
    def __init__(self, df: DataFrame):
        self._df = df

    # H3 API
    # These methods simply mirror the H3 API and apply H3 functions to all rows

    def geo_to_h3(
        self,
        resolution: int,
        lat_col: str = "lat",
        lng_col: str = "lng",
        set_index: bool = True,
    ) -> AnyDataFrame:
        """Adds H3 index to (Geo)DataFrame.

        pd.DataFrame: uses `lat_col` and `lng_col` (default `lat` and `lng`)
        gpd.GeoDataFrame: uses `geometry`

        Assumes coordinates in epsg=4326.

        Parameters
        ----------
        resolution : int
            H3 resolution
        lat_col : str
            Name of the latitude column (if used), default 'lat'
        lng_col : str
            Name of the longitude column (if used), default 'lng'
        set_index : bool
            If True, the columns with H3 addresses is set as index, default 'True'

        Returns
        -------
        (Geo)DataFrame with H3 addresses added

        See Also
        --------
        geo_to_h3_aggregate : Extended API method that aggregates points by H3 address

        Examples
        --------
        >>> df = pd.DataFrame({'lat': [50, 51], 'lng':[14, 15]})
        >>> df.h3.geo_to_h3(8)
                         lat  lng
        h3_08
        881e309739fffff   50   14
        881e2659c3fffff   51   15

        >>> df.h3.geo_to_h3(8, set_index=False)
           lat  lng            h3_08
        0   50   14  881e309739fffff
        1   51   15  881e2659c3fffff

        >>> gdf = gpd.GeoDataFrame({'val': [5, 1]},
        >>> geometry=gpd.points_from_xy(x=[14, 15], y=(50, 51)))
        >>> gdf.h3.geo_to_h3(8)
                         val                   geometry
        h3_08
        881e309739fffff    5  POINT (14.00000 50.00000)
        881e2659c3fffff    1  POINT (15.00000 51.00000)

        """
        if isinstance(self._df, gpd.GeoDataFrame):
            lngs = self._df.geometry.x
            lats = self._df.geometry.y
        else:
            lngs = self._df[lng_col]
            lats = self._df[lat_col]

        h3addresses = [
            h3.geo_to_h3(lat, lng, resolution) for lat, lng in zip(lats, lngs)
        ]

        colname = self._format_resolution(resolution)
        assign_arg = {colname: h3addresses}
        df = self._df.assign(**assign_arg)
        if set_index:
            return df.set_index(colname)
        return df

    def h3_to_geo(self) -> GeoDataFrame:
        """Add `geometry` with centroid of each H3 address to the DataFrame.
        Assumes H3 index.

        Returns
        -------
        GeoDataFrame with Point geometry

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered

        See Also
        --------
        h3_to_geo_boundary : Adds a hexagonal cell

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_to_geo()
                         val                   geometry
        881e309739fffff    5  POINT (14.00037 50.00055)
        881e2659c3fffff    1  POINT (14.99715 51.00252)

        """
        return self._apply_index_assign(
            h3.h3_to_geo,
            "geometry",
            lambda x: shapely.geometry.Point(reversed(x)),
            lambda x: gpd.GeoDataFrame(x, crs="epsg:4326"),
        )

    def h3_to_geo_boundary(self) -> GeoDataFrame:
        """Add `geometry` with H3 hexagons to the DataFrame. Assumes H3 index.

        Returns
        -------
        GeoDataFrame with H3 geometry

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_to_geo_boundary()
                         val                                           geometry
        881e309739fffff    5  POLYGON ((13.99527 50.00368, 13.99310 49.99929...
        881e2659c3fffff    1  POLYGON ((14.99201 51.00565, 14.98973 51.00133...
        """
        return self._apply_index_assign(
            wrapped_partial(h3.h3_to_geo_boundary, geo_json=True),
            "geometry",
            lambda x: shapely.geometry.Polygon(x),
            lambda x: gpd.GeoDataFrame(x, crs="epsg:4326"),
        )

    @doc_standard("h3_resolution", "containing the resolution of each H3 address")
    def h3_get_resolution(self) -> AnyDataFrame:
        """
        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_get_resolution()
                         val  h3_resolution
        881e309739fffff    5              8
        881e2659c3fffff    1              8
        """
        return self._apply_index_assign(h3.h3_get_resolution, "h3_resolution")

    @doc_standard("h3_base_cell", "containing the base cell of each H3 address")
    def h3_get_base_cell(self):
        """
        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_get_base_cell()
                         val  h3_base_cell
        881e309739fffff    5            15
        881e2659c3fffff    1            15
        """
        return self._apply_index_assign(h3.h3_get_base_cell, "h3_base_cell")

    @doc_standard("h3_is_valid", "containing the validity of each H3 address")
    def h3_is_valid(self):
        """
        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]}, index=['881e309739fffff', 'INVALID'])
        >>> df.h3.h3_is_valid()
                         val  h3_is_valid
        881e309739fffff    5         True
        INVALID            1        False
        """
        return self._apply_index_assign(h3.h3_is_valid, "h3_is_valid")

    @doc_standard(
        "h3_k_ring", "containing a list H3 addresses within a distance of `k`"
    )
    def k_ring(self, k: int = 1, explode: bool = False) -> AnyDataFrame:
        """
        Parameters
        ----------
        k : int
            the distance from the origin H3 address. Default k = 1
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False

        See Also
        --------
        k_ring_smoothing : Extended API method that distributes numeric values
            to the k-ring cells

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.k_ring(1)
                         val                                          h3_k_ring
        881e309739fffff    5  [881e30973dfffff, 881e309703fffff, 881e309707f...
        881e2659c3fffff    1  [881e2659ddfffff, 881e2659c3fffff, 881e2659cbf...

        >>> df.h3.k_ring(1, explode=True)
                         val        h3_k_ring
        881e2659c3fffff    1  881e2659ddfffff
        881e2659c3fffff    1  881e2659c3fffff
        881e2659c3fffff    1  881e2659cbfffff
        881e2659c3fffff    1  881e2659d5fffff
        881e2659c3fffff    1  881e2659c7fffff
        881e2659c3fffff    1  881e265989fffff
        881e2659c3fffff    1  881e2659c1fffff
        881e309739fffff    5  881e30973dfffff
        881e309739fffff    5  881e309703fffff
        881e309739fffff    5  881e309707fffff
        881e309739fffff    5  881e30973bfffff
        881e309739fffff    5  881e309715fffff
        881e309739fffff    5  881e309739fffff
        881e309739fffff    5  881e309731fffff
        """
        func = wrapped_partial(h3.k_ring, k=k)
        column_name = "h3_k_ring"
        if explode:
            return self._apply_index_explode(func, column_name, list)
        return self._apply_index_assign(func, column_name, list)

    @doc_standard(
        "h3_hex_ring",
        "containing a list H3 addresses forming a hollow hexagonal ring"
        "at a distance `k`",
    )
    def hex_ring(self, k: int = 1, explode: bool = False) -> AnyDataFrame:
        """
        Parameters
        ----------
        k : int
            the distance from the origin H3 address. Default k = 1
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.hex_ring(1)
                         val                                        h3_hex_ring
        881e309739fffff    5  [881e30973dfffff, 881e309703fffff, 881e309707f...
        881e2659c3fffff    1  [881e2659ddfffff, 881e2659cbfffff, 881e2659d5f...
        >>> df.h3.hex_ring(1, explode=True)
                         val      h3_hex_ring
        881e2659c3fffff    1  881e2659ddfffff
        881e2659c3fffff    1  881e2659cbfffff
        881e2659c3fffff    1  881e2659d5fffff
        881e2659c3fffff    1  881e2659c7fffff
        881e2659c3fffff    1  881e265989fffff
        881e2659c3fffff    1  881e2659c1fffff
        881e309739fffff    5  881e30973dfffff
        881e309739fffff    5  881e309703fffff
        881e309739fffff    5  881e309707fffff
        881e309739fffff    5  881e30973bfffff
        881e309739fffff    5  881e309715fffff
        881e309739fffff    5  881e309731fffff
        """
        func = wrapped_partial(h3.hex_ring, k=k)
        column_name = "h3_hex_ring"
        if explode:
            return self._apply_index_explode(func, column_name, list)
        return self._apply_index_assign(func, column_name, list)

    @doc_standard("h3_{resolution}", "containing the parent of each H3 address")
    def h3_to_parent(self, resolution: int = None) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int or None
            H3 resolution. If None, then returns the direct parent of each H3 cell.

        See Also
        --------
        h3_to_parent_aggregate : Extended API method that aggregates cells by their
            parent cell

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_to_parent(5)
                         val            h3_05
        881e309739fffff    5  851e3097fffffff
        881e2659c3fffff    1  851e265bfffffff
        """
        # TODO: Test `h3_parent` case
        column = self._format_resolution(resolution) if resolution else "h3_parent"
        return self._apply_index_assign(
            wrapped_partial(h3.h3_to_parent, res=resolution), column
        )

    @doc_standard("h3_center_child", "containing the center child of each H3 address")
    def h3_to_center_child(self, resolution: int = None) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int or None
            H3 resolution. If none, then returns the child of resolution
            directly below that of each H3 cell

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                    index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_to_center_child()
                         val  h3_center_child
        881e309739fffff    5  891e3097383ffff
        881e2659c3fffff    1  891e2659c23ffff
        """
        return self._apply_index_assign(
            wrapped_partial(h3.h3_to_center_child, res=resolution), "h3_center_child"
        )

    @doc_standard(
        COLUMN_H3_POLYFILL,
        "containing a list H3 addresses whose centroid falls into the Polygon",
    )
    def polyfill(self, resolution: int, explode: bool = False) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int
            H3 resolution
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False

        See Also
        --------
        polyfill_resample : Extended API method that distributes the polygon's values
            to the H3 cells contained in it

        Examples
        --------
        >>> from shapely.geometry import box
        >>> gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1)])
        >>> gdf.h3.polyfill(4)
                                                    geometry                                        h3_polyfill
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  [84754e3ffffffff, 84754c7ffffffff, 84754c5ffff...  # noqa E501
        >>> gdf.h3.polyfill(4, explode=True)
                                                    geometry      h3_polyfill
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754e3ffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754c7ffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754c5ffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754ebffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754edffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754e1ffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  84754e9ffffffff
        0  POLYGON ((1.00000 0.00000, 1.00000 1.00000, 0....  8475413ffffffff
        """

        def func(row):
            return list(polyfill(row.geometry, resolution, True))

        result = self._df.apply(func, axis=1)

        if not explode:
            assign_args = {COLUMN_H3_POLYFILL: result}
            return self._df.assign(**assign_args)

        result = result.explode().to_frame(COLUMN_H3_POLYFILL)

        return self._df.join(result)

    @doc_standard("h3_cell_area", "containing the area of each H3 address")
    def cell_area(
        self, unit: Literal["km^2", "m^2", "rads^2"] = "km^2"
    ) -> AnyDataFrame:
        """
        Parameters
        ----------
        unit : str, options: 'km^2', 'm^2', or 'rads^2'
            Unit for area result. Default: 'km^2`

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.cell_area()
                         val  h3_cell_area
        881e309739fffff    5      0.695651
        881e2659c3fffff    1      0.684242
        """
        return self._apply_index_assign(
            wrapped_partial(h3.cell_area, unit=unit), "h3_cell_area"
        )

    # H3-Pandas Extended API
    # These methods extend the API to provide a convenient way to simplify workflows

    def geo_to_h3_aggregate(
        self,
        resolution: int,
        operation: Union[dict, str, Callable] = "sum",
        lat_col: str = "lat",
        lng_col: str = "lng",
        return_geometry: bool = True,
    ) -> DataFrame:
        """Adds H3 index to DataFrame, groups points with the same index
        and performs `operation`.

        pd.DataFrame: uses `lat_col` and `lng_col` (default `lat` and `lng`)
        gpd.GeoDataFrame: uses `geometry`

        Parameters
        ----------
        resolution : int
            H3 resolution
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'
        lat_col : str
            Name of the latitude column (if used), default 'lat'
        lng_col : str
            Name of the longitude column (if used), default 'lng'
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the hexagonal cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame aggregated by H3 address into which each row's point falls

        See Also
        --------
        geo_to_h3 : H3 API method upon which this function builds

        Examples
        --------
        >>> df = pd.DataFrame({'lat': [50, 51], 'lng':[14, 15], 'val': [10, 1]})
        >>> df.h3.geo_to_h3(1)
                         lat  lng  val
        h3_01
        811e3ffffffffff   50   14   10
        811e3ffffffffff   51   15    1
        >>> df.h3.geo_to_h3_aggregate(1)
                         val                                           geometry
        h3_01
        811e3ffffffffff   11  POLYGON ((12.34575 50.55428, 12.67732 46.40696...
        >>> df = pd.DataFrame({'lat': [50, 51], 'lng':[14, 15], 'val': [10, 1]})
        >>> df.h3.geo_to_h3_aggregate(1, operation='mean')
                         val                                           geometry
        h3_01
        811e3ffffffffff  5.5  POLYGON ((12.34575 50.55428, 12.67732 46.40696...
        >>> df.h3.geo_to_h3_aggregate(1, return_geometry=False)
                         val
        h3_01
        811e3ffffffffff   11
        """
        grouped = pd.DataFrame(
            self.geo_to_h3(resolution, lat_col, lng_col, False)
            .drop(columns=[lat_col, lng_col, "geometry"], errors="ignore")
            .groupby(self._format_resolution(resolution))
            .agg(operation)
        )
        return grouped.h3.h3_to_geo_boundary() if return_geometry else grouped

    def h3_to_parent_aggregate(
        self,
        resolution: int,
        operation: Union[dict, str, Callable] = "sum",
        return_geometry: bool = True,
    ) -> GeoDataFrame:
        """Assigns parent cell to each row, groups by it and performs `operation`.
        Assumes H3 index.

        Parameters
        ----------
        resolution : int
            H3 resolution
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the hexagonal cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame aggregated by the parent of each H3 address

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered

        See Also
        --------
        h3_to_parent : H3 API method upon which this function builds

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.h3_to_parent(1)
                         val            h3_01
        881e309739fffff    5  811e3ffffffffff
        881e2659c3fffff    1  811e3ffffffffff
        >>> df.h3.h3_to_parent_aggregate(1)
                         val                                           geometry
        h3_01
        811e3ffffffffff    6  POLYGON ((12.34575 50.55428, 12.67732 46.40696...
        >>> df.h3.h3_to_parent_aggregate(1, operation='mean')
                         val                                           geometry
        h3_01
        811e3ffffffffff    3  POLYGON ((12.34575 50.55428, 12.67732 46.40696...
        >>> df.h3.h3_to_parent_aggregate(1, return_geometry=False)
                         val
        h3_01
        811e3ffffffffff    6
        """
        parent_h3addresses = [
            catch_invalid_h3_address(h3.h3_to_parent)(h3address, resolution)
            for h3address in self._df.index
        ]
        h3_parent_column = self._format_resolution(resolution)
        kwargs_assign = {h3_parent_column: parent_h3addresses}
        grouped = (
            self._df.assign(**kwargs_assign)
            .groupby(h3_parent_column)[[c for c in self._df.columns if c != "geometry"]]
            .agg(operation)
        )

        return grouped.h3.h3_to_geo_boundary() if return_geometry else grouped

    # TODO: Needs to allow for handling relative values (e.g. percentage)
    # TODO: Will possibly fail in many cases (what are the existing columns?)
    # TODO: New cell behaviour
    def k_ring_smoothing(
        self,
        k: int = None,
        weights: Sequence[float] = None,
        return_geometry: bool = True,
    ) -> AnyDataFrame:
        """Experimental. Creates a k-ring around each input cell and distributes
        the cell's values.

        The values are distributed either
         - uniformly (by setting `k`) or
         - by weighing their values using `weights`.

        Only numeric columns are modified.

        Parameters
        ----------
        k : int
            The distance from the origin H3 address
        weights : Sequence[float]
            Weighting of the values based on the distance from the origin.
            First weight corresponds to the origin.
            Values are be normalized to add up to 1.
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the hexagonal cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame with smoothed values

        See Also
        --------
        k_ring : H3 API method upon which this method builds

        Examples
        --------
        >>> df = pd.DataFrame({'val': [5, 1]},
        >>>                   index=['881e309739fffff', '881e2659c3fffff'])
        >>> df.h3.k_ring_smoothing(1)
                              val                                           geometry
        h3_k_ring
        881e265989fffff  0.142857  POLYGON ((14.99488 50.99821, 14.99260 50.99389...
        881e2659c1fffff  0.142857  POLYGON ((14.97944 51.00758, 14.97717 51.00326...
        881e2659c3fffff  0.142857  POLYGON ((14.99201 51.00565, 14.98973 51.00133...
        881e2659c7fffff  0.142857  POLYGON ((14.98231 51.00014, 14.98004 50.99582...
        881e2659cbfffff  0.142857  POLYGON ((14.98914 51.01308, 14.98687 51.00877...
        881e2659d5fffff  0.142857  POLYGON ((15.00458 51.00371, 15.00230 50.99940...
        881e2659ddfffff  0.142857  POLYGON ((15.00171 51.01115, 14.99943 51.00684...
        881e309703fffff  0.714286  POLYGON ((13.99235 50.01119, 13.99017 50.00681...
        881e309707fffff  0.714286  POLYGON ((13.98290 50.00555, 13.98072 50.00116...
        881e309715fffff  0.714286  POLYGON ((14.00473 50.00932, 14.00255 50.00494...
        881e309731fffff  0.714286  POLYGON ((13.99819 49.99617, 13.99602 49.99178...
        881e309739fffff  0.714286  POLYGON ((13.99527 50.00368, 13.99310 49.99929...
        881e30973bfffff  0.714286  POLYGON ((14.00765 50.00181, 14.00547 49.99742...
        881e30973dfffff  0.714286  POLYGON ((13.98582 49.99803, 13.98364 49.99365...
        >>> df.h3.k_ring_smoothing(weights=[2, 1])
                           val                                           geometry
        h3_hex_ring
        881e265989fffff  0.125  POLYGON ((14.99488 50.99821, 14.99260 50.99389...
        881e2659c1fffff  0.125  POLYGON ((14.97944 51.00758, 14.97717 51.00326...
        881e2659c3fffff  0.250  POLYGON ((14.99201 51.00565, 14.98973 51.00133...
        881e2659c7fffff  0.125  POLYGON ((14.98231 51.00014, 14.98004 50.99582...
        881e2659cbfffff  0.125  POLYGON ((14.98914 51.01308, 14.98687 51.00877...
        881e2659d5fffff  0.125  POLYGON ((15.00458 51.00371, 15.00230 50.99940...
        881e2659ddfffff  0.125  POLYGON ((15.00171 51.01115, 14.99943 51.00684...
        881e309703fffff  0.625  POLYGON ((13.99235 50.01119, 13.99017 50.00681...
        881e309707fffff  0.625  POLYGON ((13.98290 50.00555, 13.98072 50.00116...
        881e309715fffff  0.625  POLYGON ((14.00473 50.00932, 14.00255 50.00494...
        881e309731fffff  0.625  POLYGON ((13.99819 49.99617, 13.99602 49.99178...
        881e309739fffff  1.250  POLYGON ((13.99527 50.00368, 13.99310 49.99929...
        881e30973bfffff  0.625  POLYGON ((14.00765 50.00181, 14.00547 49.99742...
        881e30973dfffff  0.625  POLYGON ((13.98582 49.99803, 13.98364 49.99365...
        >>> df.h3.k_ring_smoothing(1, return_geometry=False)
                              val
        h3_k_ring
        881e265989fffff  0.142857
        881e2659c1fffff  0.142857
        881e2659c3fffff  0.142857
        881e2659c7fffff  0.142857
        881e2659cbfffff  0.142857
        881e2659d5fffff  0.142857
        881e2659ddfffff  0.142857
        881e309703fffff  0.714286
        881e309707fffff  0.714286
        881e309715fffff  0.714286
        881e309731fffff  0.714286
        881e309739fffff  0.714286
        881e30973bfffff  0.714286
        881e30973dfffff  0.714286
        """
        if sum([weights is None, k is None]) != 1:
            raise ValueError("Exactly one of `k` and `weights` must be set.")

        # If weights are all equal, use the computationally simpler option
        if (weights is not None) and (len(set(weights)) == 1):
            k = len(weights) - 1
            weights = None

        # Unweighted case
        if weights is None:
            result = pd.DataFrame(
                self._df.h3.k_ring(k, explode=True)
                .groupby("h3_k_ring")
                .sum()
                .divide((1 + 3 * k * (k + 1)))
            )

            return result.h3.h3_to_geo_boundary() if return_geometry else result

        if len(weights) == 0:
            raise ValueError("Weights cannot be empty.")

        # Weighted case
        weights = np.array(weights)
        multipliers = np.array([1] + [i * 6 for i in range(1, len(weights))])
        weights = weights / (weights * multipliers).sum()

        # This should be exploded hex ring
        def weighted_hex_ring(df, k, normalized_weight):
            return df.h3.hex_ring(k, explode=True).h3._multiply_numeric(
                normalized_weight
            )

        result = (
            pd.concat(
                [
                    weighted_hex_ring(self._df, i, weights[i])
                    for i in range(len(weights))
                ]
            )
            .groupby("h3_hex_ring")
            .sum()
        )

        return result.h3.h3_to_geo_boundary() if return_geometry else result

    def polyfill_resample(
        self, resolution: int, return_geometry: bool = True
    ) -> AnyDataFrame:
        """Experimental. Currently essentially polyfill(..., explode=True) that
        sets the H3 index and adds the H3 cell geometry.

        Parameters
        ----------
        resolution : int
            H3 resolution
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the hexagonal cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame with H3 cells with centroids within the input polygons.

        See Also
        --------
        polyfill : H3 API method upon which this method builds

        Examples
        --------
        >>> from shapely.geometry import box
        >>> gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1)])
        >>> gdf.h3.polyfill_resample(4)
                         index                                           geometry
        h3_polyfill
        84754e3ffffffff      0  POLYGON ((0.33404 -0.11975, 0.42911 0.07901, 0...
        84754c7ffffffff      0  POLYGON ((0.92140 -0.03115, 1.01693 0.16862, 0...
        84754c5ffffffff      0  POLYGON ((0.91569 0.33807, 1.01106 0.53747, 0....
        84754ebffffffff      0  POLYGON ((0.62438 0.10878, 0.71960 0.30787, 0....
        84754edffffffff      0  POLYGON ((0.32478 0.61394, 0.41951 0.81195, 0....
        84754e1ffffffff      0  POLYGON ((0.32940 0.24775, 0.42430 0.44615, 0....
        84754e9ffffffff      0  POLYGON ((0.61922 0.47649, 0.71427 0.67520, 0....
        8475413ffffffff      0  POLYGON ((0.91001 0.70597, 1.00521 0.90497, 0....
        """
        result = self._df.h3.polyfill(resolution, explode=True)
        uncovered_rows = result[COLUMN_H3_POLYFILL].isna()
        n_uncovered_rows = uncovered_rows.sum()
        if n_uncovered_rows > 0:
            warnings.warn(
                f"{n_uncovered_rows} rows did not generate a H3 cell."
                "Consider using a finer resolution."
            )
            result = result.loc[~uncovered_rows]

        result = result.reset_index().set_index(COLUMN_H3_POLYFILL)

        return result.h3.h3_to_geo_boundary() if return_geometry else result

    # Private methods

    def _apply_index_assign(
        self,
        func: Callable,
        column_name: str,
        processor: Callable = lambda x: x,
        finalizer: Callable = lambda x: x,
    ) -> Any:
        """Helper method. Applies `func` to index and assigns the result to `column`.

        Parameters
        ----------
        func : Callable
            single-argument function to be applied to each H3 address
        column_name : str
            name of the resulting column
        processor : Callable
            (Optional) further processes the result of func. Default: identity
        finalizer : Callable
            (Optional) further processes the resulting dataframe. Default: identity

        Returns
        -------
        Dataframe with column `column` containing the result of `func`.
        If using `finalizer`, can return anything the `finalizer` returns.
        """
        func = catch_invalid_h3_address(func)
        result = [processor(func(h3address)) for h3address in self._df.index]
        assign_args = {column_name: result}
        return finalizer(self._df.assign(**assign_args))

    def _apply_index_explode(
        self,
        func: Callable,
        column_name: str,
        processor: Callable = lambda x: x,
        finalizer: Callable = lambda x: x,
    ) -> Any:
        """Helper method. Applies a list-making `func` to index and performs
        a vertical explode.
        Any additional values are simply copied to all the rows.

        Parameters
        ----------
        func : Callable
            single-argument function to be applied to each H3 address
        column_name : str
            name of the resulting column
        processor : Callable
            (Optional) further processes the result of func. Default: identity
        finalizer : Callable
            (Optional) further processes the resulting dataframe. Default: identity

        Returns
        -------
        Dataframe with column `column` containing the result of `func`.
        If using `finalizer`, can return anything the `finalizer` returns.
        """
        func = catch_invalid_h3_address(func)
        result = (
            pd.DataFrame.from_dict(
                {h3address: processor(func(h3address)) for h3address in self._df.index},
                orient="index",
            )
            .stack()
            .to_frame(column_name)
            .reset_index(level=1, drop=True)
        )
        result = self._df.join(result)
        return finalizer(result)

    # TODO: types, doc, ..
    def _multiply_numeric(self, value):
        columns_numeric = self._df.select_dtypes(include=["number"]).columns
        assign_args = {
            column: self._df[column].multiply(value) for column in columns_numeric
        }
        return self._df.assign(**assign_args)

    @staticmethod
    def _format_resolution(resolution: int) -> str:
        return f"h3_{str(resolution).zfill(2)}"
