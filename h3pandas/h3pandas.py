from typing import Union, Callable, Sequence
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


@pd.api.extensions.register_dataframe_accessor('h3')
class H3Accessor:


    def __init__(self, df: DataFrame):
        self._df = df

    # H3 API
    # These methods simply mirror the H3 API and apply H3 functions to all rows

    def geo_to_h3(self,
                  resolution: int,
                  lat_col: str = 'lat',
                  lng_col: str = 'lng',
                  set_index: bool = True) -> AnyDataFrame:
        """Adds H3 index to (Geo)DataFrame.

        pd.DataFrame: uses `lat_col` and `lng_col` (default `lat` and `lng`)
        gpd.GeoDataFrame: uses `geometry`

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
        """
        if isinstance(self._df, gpd.GeoDataFrame):
            lngs = self._df.geometry.x
            lats = self._df.geometry.y
            h3addresses = [h3.geo_to_h3(lat, lng, resolution) for lat, lng in zip(lats, lngs)]
        else:
            h3addresses = self._df.apply(lambda x: h3.geo_to_h3(x[lat_col], x[lng_col], resolution), axis=1)

        colname = self._format_resolution(resolution)
        assign_arg = {colname: h3addresses}
        df = self._df.assign(**assign_arg)
        if set_index:
            return df.set_index(colname)
        return df


    # TODO: Test
    def h3_to_geo(self) -> GeoDataFrame:
        """Add `geometry` with centroid of each H3 address to the DataFrame. Assumes H3 index.

        Returns
        -------
        GeoDataFrame with Point geometry

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered
        """
        return self._apply_index_assign(h3.h3_to_geo,
                                        'geometry',
                                        lambda x: shapely.geometry.Point(reversed(x)),
                                        lambda x: gpd.GeoDataFrame(x, crs='epsg:4326'))


    def h3_to_geo_boundary(self) -> GeoDataFrame:
        """Add `geometry` with H3 hexagons to the DataFrame. Assumes H3 index.

        Returns
        -------
        GeoDataFrame with H3 geometry

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered
        """
        return self._apply_index_assign(wrapped_partial(h3.h3_to_geo_boundary, geo_json=True),
                                        'geometry',
                                        lambda x: shapely.geometry.Polygon(x),
                                        lambda x: gpd.GeoDataFrame(x, crs='epsg:4326'))


    @doc_standard('h3_resolution', 'containing the resolution of each H3 address')
    def h3_get_resolution(self) -> AnyDataFrame:
        return self._apply_index_assign(h3.h3_get_resolution, 'h3_resolution')


    # TODO: test
    @doc_standard('h3_base_cell', 'containing the base cell of each H3 address')
    def h3_get_base_cell(self):
        return self._apply_index_assign(h3.h3_get_base_cell, 'h3_base_cell')


    # TODO: test
    @doc_standard('h3_is_valid', 'containing the validity of each H3 address')
    def h3_is_valid(self):
        return self._apply_index_assign(h3.h3_is_valid, 'h3_is_valid')


    # TODO: Test
    # TODO: Consider 'explode' option (same goes for all list-making methods)
    @doc_standard('h3_k_ring', 'containing a list H3 addresses within a distance of `k`')
    def k_ring(self, k: int = 1) -> AnyDataFrame:
        """
        Parameters
        ----------
        k : int
            the distance from the origin H3 address. Default k = 1
        """
        return self._apply_index_assign(wrapped_partial(h3.k_ring, k=k), 'h3_k_ring', lambda x: list(x))

    # TODO: Test
    # TODO: Doc
    @doc_standard('h3_k_ring', 'containing a list H3 addresses forming a hollow hexagonal ring'
                               'at a distance `k`')
    def hex_ring(self,
                 k: int = 1,
                 explode: bool = False) -> AnyDataFrame:
        """
        Parameters
        ----------
        k : int
            the distance from the origin H3 address. Default k = 1
        explode : bool
        """
        return self._apply_index_assign(wrapped_partial(h3.hex_ring, k=k), 'h3_hex_ring', lambda x: list(x))


    @doc_standard('h3_{resolution}', 'containing the parent of each H3 address')
    def h3_to_parent(self, resolution: int = None) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int or None
            H3 resolution. If None, then returns the direct parent of each H3 cell.
        """
        # TODO: Test `h3_parent` case
        column = self._format_resolution(resolution) if resolution else 'h3_parent'
        return self._apply_index_assign(wrapped_partial(h3.h3_to_parent, res=resolution), column)


    # TODO: Test
    @doc_standard('h3_center_child', 'containing the center child of each H3 address')
    def h3_to_center_child(self, resolution: int = None) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int or None
            H3 resolution. If none, then returns the child of resolution directly below that of each H3 cell
        """
        return self._apply_index_assign(wrapped_partial(h3.h3_to_center_child, res=resolution),
                                        'h3_center_child')


    # TODO: Test
    # TODO: Geometry test?
    @doc_standard(COLUMN_H3_POLYFILL,
                  'containing a list H3 addresses whose centroid falls into the Polygon')
    def polyfill(self,
                 resolution: int,
                 explode: bool = False) -> AnyDataFrame:
        """
        Parameters
        ----------
        resolution : int
            H3 resolution
        explode : bool

        """

        def func(geometry): return list(polyfill(geometry, resolution, True))
        if explode:
            def func(geometry): return pd.Series(func(geometry))

        result = self._df.geometry.apply(func)
        if not explode:
            result = result.rename('h3_polyfill')
        return self._df.join(result)


    # TODO: Test
    @doc_standard('h3_cell_area', 'containing the area of each H3 address')
    def h3_cell_area(self, unit: Literal['km^2', 'm^2', 'rads^2'] = 'km^2') -> AnyDataFrame:
        """
        Parameters
        ----------
        unit : str, options: 'km^2', 'm^2', or 'rads^2'
            Unit for area result. Default: 'km^2`
        """
        return self._apply_index_assign(wrapped_partial(h3.cell_area, unit=unit), 'h3_cell_area')


    # TODO: The semantics of this are no longer correct. Consider a different naming/description
    # Aggregate methods
    # These methods extend the API to provide a convenient way to aggregate the results by their H3 address

    def geo_to_h3_aggregate(self,
                            resolution: int,
                            operation: Union[dict, str, Callable] = 'sum',
                            lat_col: str = 'lat',
                            lng_col: str = 'lng' ) -> DataFrame:
        """Adds H3 index to DataFrame, groups points with the same index and performs `operation`

        Warning: Geographic information gets lost, returns a DataFrame
            - if you wish to retain it, consider using `geo_to_h3` instead.
            - if you with to add H3 geometry, chain with `h3_to_geo_boundary`

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


        Returns
        -------
        DataFrame aggregated by H3 address into which each row's point falls
        """
        return pd.DataFrame(self.geo_to_h3(resolution, lat_col, lng_col, False)
                            .drop(columns=[lat_col, lng_col, 'geometry'], errors='ignore')
                            .groupby(self._format_resolution(resolution))
                            .agg(operation))


    def h3_to_parent_aggregate(self,
                               resolution: int,
                               operation: Union[dict, str, Callable] = 'sum') -> GeoDataFrame:
        """Assigns parent cell to each row, groups by it and performs `operation`. Assumes H3 index.

        Parameters
        ----------
        resolution : int
            H3 resolution
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'

        Returns
        -------
        GeoDataFrame aggregated by the parent of each H3 address

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered
        """
        # TODO: Unified has_geometry behaviour
        has_geometry = 'geometry' in self._df.columns

        parent_h3addresses = [catch_invalid_h3_address(h3.h3_to_parent)(h3address, resolution)
                              for h3address in self._df.index]
        h3_parent_column = self._format_resolution(resolution)
        kwargs_assign = {h3_parent_column: parent_h3addresses}
        grouped = (self._df
                   .assign(**kwargs_assign)
                   .groupby(h3_parent_column)[[c for c in self._df.columns if c != 'geometry']]
                   .agg(operation))

        if has_geometry:
            return grouped.h3.h3_to_geo_boundary()
        else:
            return grouped


    # TODO: Doc
    # TODO: Test
    # TODO: Test, k=3 should be same as [1,1,1,1,1]
    # TODO: Will likely fail in many cases (what are the existing columns?)
    # TODO: New cell behaviour
    # TODO: Re-do properly
    def k_ring_smoothing(self,
                         k: int,
                         weights: Sequence[float] = None) -> AnyDataFrame:
        """Experimental.

        Parameters
        ----------
        k : int
        weights : Sequence[float] of length k

        Returns
        -------

        """
        if weights is None:
            return (self._df
                    .apply(lambda x: pd.Series(list(h3.k_ring(x.name, k))), axis=1).stack()
                    .to_frame('h3_k_ring').reset_index(1, drop=True)
                    .join(self._df)
                    .groupby('h3_k_ring').sum().divide((1 + 3 * k * (k + 1))))

        weights = np.array(weights)
        multipliers = np.array([1] + [i * 6 for i in range(1, len(weights))])
        weights = weights / (weights * multipliers).sum()

        # This should be exploded hex ring
        def weighted_hex_ring(df, k, normalized_weight):
            return (df
                    .apply(lambda x: pd.Series(list(h3.hex_ring(x.name, k))), axis=1).stack()
                    .to_frame('h3_hex_ring').reset_index(1, drop=True)
                    .join(df)
                    .h3._multiply_numeric(normalized_weight))

        return (pd.concat([weighted_hex_ring(self._df, i, weights[i]) for i in range(len(weights))])
                .groupby('h3_hex_ring')
                .sum()
                .h3.h3_to_geo_boundary())








    # TODO: Test
    # TODO: Implement
    # TODO: Provide a warning if sums don't agree or sth like that? For uncovered polygons
    def polyfill_resample(self, resolution: int) -> AnyDataFrame:
        """Experimental

        Parameters
        ----------
        resolution : int

        Returns
        -------

        """

        return (self._df
                .h3.polyfill(resolution)
                [COLUMN_H3_POLYFILL]
                .apply(lambda x: pd.Series(x)).stack()
                .to_frame(COLUMN_H3_POLYFILL).reset_index(level=1, drop=True)
                .join(self._df)
                .reset_index()
                .set_index(COLUMN_H3_POLYFILL)
                .h3.h3_to_geo_boundary())


    # Private methods

    def _apply_index_assign(self,
                            func: Callable,
                            column: str,
                            processor: Callable = lambda x: x,
                            finalizer: Callable = lambda x: x):
        """Helper method. Applies `func` to index and assigns the result to `column`.

        Parameters
        ----------
        func : Callable
            single-argument function to be applied to each H3 address
        column : str
            name of the resulting column
        processor : Callable
            (Optional) further processes the result of func. Default: identity
        finalizer : Callable
            (Optional) further processes the resulting dataframe. Default: identity

        Returns
        -------
        Dataframe with column `column` containing the result of `func`.
        """
        func = catch_invalid_h3_address(func)
        result = [processor(func(h3address)) for h3address in self._df.index]
        assign_args = {column: result}
        return finalizer(self._df.assign(**assign_args))


    # TODO: types, doc, ..
    def _multiply_numeric(self, value):
        columns_numeric = self._df.select_dtypes(include=['number']).columns
        assign_args = {column: self._df[column].multiply(value) for column in columns_numeric}
        return self._df.assign(**assign_args)


    @staticmethod
    def _format_resolution(resolution: int) -> str:
        return f'h3_{str(resolution).zfill(2)}'
