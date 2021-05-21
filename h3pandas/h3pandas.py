from typing import Union, Callable

import shapely
import pandas as pd
import geopandas as gpd

from h3 import h3
from h3 import H3CellError
from pandas.core.frame import DataFrame
from geopandas.geodataframe import GeoDataFrame
AnyDataFrame = Union[DataFrame, GeoDataFrame]


@pd.api.extensions.register_dataframe_accessor('h3')
class H3Accessor:
    def __init__(self, df: DataFrame):
        self._df = df

    # H3 API
    # These functions simply mirror the H3 API and apply H3 functions # to all rows

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

        colname = f'h3_{resolution}'
        assign_arg = {colname: h3addresses}
        df = self._df.assign(**assign_arg)
        if set_index:
            return df.set_index(colname)
        return df

    def h3_to_geo_boundary(self) -> GeoDataFrame:
        """Add `geometry` with H3 hexagons to the DataFrame. Assumes H3 index.

        Returns
        -------
        GeoDataFrame with H3 geometry

        Raises
        ------
        TypeError
            When an invalid H3 address is encountered
        """

        def _to_polygon(h):
            try:
                return shapely.geometry.Polygon(h3.h3_to_geo_boundary(h, True))  # GeoPandas is lng/lat
            except (TypeError, H3CellError, ValueError):
                raise TypeError(f"H3 address was not recognized: {h}.")

        geometries = [_to_polygon(h3address) for h3address in self._df.index]

        return gpd.GeoDataFrame(self._df, geometry=geometries, crs='epsg:4326')

    def h3_to_parent(self,
                     resolution: int) -> AnyDataFrame:
        """Adds the column `h3_parent` containing the parent of each H3 address. Assumes H3 index.

        Parameters
        ----------
        resolution : int
            H3 resolution

        Returns
        -------
        (Geo)DataFrame with `h3_parent` column added
        """
        parent_h3addresses = [h3.h3_to_parent(h3address, resolution) for h3address in self._df.index]
        return self._df.assign(h3_parent=parent_h3addresses)

    def h3_get_resolution(self) -> AnyDataFrame:
        """Adds the column `h3_resolution` containing the resolution of each H3 address. Assumes H3 index.

        Returns
        -------
        Geo(DataFrame) with `h3_resolution` column added
        """

        resolutions = [h3.h3_get_resolution(h3address) for h3address in self._df.index]
        return self._df.assign(h3_resolution=resolutions)

    # Aggregate functions
    # These functions extend the API to provide a convenient way to aggregate the results by their H3 address

    def geo_to_h3_aggregate(self,
                            resolution: int,
                            lat_col: str = 'lat',
                            lng_col: str = 'lng',
                            operation: Union[dict, str, Callable] = 'sum') -> DataFrame:
        """Adds H3 index to DataFrame. Groups points with the same index and performs `operation`

        Warning: Geographic information gets lost, returns a DataFrame
        - if you wish to retain it, consider using `geo_to_h3` instead.
        - if you with to add H3 geometry, chain with `h3_to_geo_boundary`

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
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'


        Returns
        -------
        DataFrame aggregated by H3 address into which each row's point falls
        """
        return pd.DataFrame(self.geo_to_h3(resolution, lat_col, lng_col, False)
                            .agg(operation)
                            .drop(columns=[lat_col, lng_col, 'geometry'], errors='ignore'))

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
        """
        has_geometry = 'geometry' in self._df.columns

        parent_h3addresses = [h3.h3_to_parent(h3address, resolution) for h3address in self._df.index]
        grouped = (self._df
                   .groupby(parent_h3addresses)[[c for c in self._df.columns if c != 'geometry']]
                   .agg(operation))

        if has_geometry:
            return grouped.h3.h3_to_geo_boundary()
        else:
            return grouped
