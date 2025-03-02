from typing import Union, Set, Iterator
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import transform
import h3
from .decorator import sequential_deduplication


MultiPolyOrPoly = Union[Polygon, MultiPolygon]
MultiLineOrLine = Union[LineString, MultiLineString]


def polyfill(geometry: MultiPolyOrPoly, resolution: int) -> Set[str]:
    """h3.polyfill accepting a shapely (Multi)Polygon

    Parameters
    ----------
    geometry : Polygon or Multipolygon
        Polygon to fill
    resolution : int
        H3 resolution of the filling cells

    Returns
    -------
    Set of H3 addresses

    Raises
    ------
    TypeError if geometry is not a Polygon or MultiPolygon
    """
    if isinstance(geometry, (Polygon, MultiPolygon)):
        h3shape = h3.geo_to_h3shape(geometry)
        return set(h3.polygon_to_cells(h3shape, resolution))
    else:
        raise TypeError(f"Unknown type {type(geometry)}")


def cell_to_boundary_lng_lat(h3_address: str) -> MultiLineString:
    """h3.h3_to_geo_boundary equivalent for shapely

    Parameters
    ----------
    h3_address : str
        H3 address to convert to a boundary

    Returns
    -------
    MultiLineString representing the H3 cell boundary
    """
    return _switch_lat_lng(Polygon(h3.cell_to_boundary(h3_address)))


def _switch_lat_lng(geometry: MultiPolyOrPoly) -> MultiPolyOrPoly:
    """Switches the order of coordinates in a Polygon or MultiPolygon

    Parameters
    ----------
    geometry : Polygon or Multipolygon
        Polygon to switch coordinates

    Returns
    -------
    Polygon or Multipolygon with switched coordinates
    """
    return transform(lambda x, y: (y, x), geometry)


@sequential_deduplication
def linetrace(geometry: MultiLineOrLine, resolution: int) -> Iterator[str]:
    """h3.polyfill equivalent for shapely (Multi)LineString
    Does not represent lines with duplicate sequential cells,
    but cells may repeat non-sequentially to represent
    self-intersections

    Parameters
    ----------
    geometry : LineString or MultiLineString
        Line to trace with H3 cells
    resolution : int
        H3 resolution of the tracing cells

    Returns
    -------
    Set of H3 addresses

    Raises
    ------
    TypeError if geometry is not a LineString or a MultiLineString
    """
    if isinstance(geometry, MultiLineString):
        # Recurse after getting component linestrings from the multiline
        for line in map(lambda geom: linetrace(geom, resolution), geometry.geoms):
            yield from line
    elif isinstance(geometry, LineString):
        coords = zip(geometry.coords, geometry.coords[1:])
        while (vertex_pair := next(coords, None)) is not None:
            i, j = vertex_pair
            a = h3.latlng_to_cell(*i[::-1], resolution)
            b = h3.latlng_to_cell(*j[::-1], resolution)
            yield from h3.grid_path_cells(a, b)  # inclusive of a and b
    else:
        raise TypeError(f"Unknown type {type(geometry)}")
