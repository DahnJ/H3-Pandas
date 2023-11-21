from typing import Union, Set, Tuple, List, Iterator
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from h3 import h3
from .decorator import sequential_deduplication

MultiPolyOrPoly = Union[Polygon, MultiPolygon]
MultiLineOrLine = Union[LineString, MultiLineString]


def _extract_coords(polygon: Polygon) -> Tuple[List, List[List]]:
    """Extract the coordinates of outer and inner rings from a Polygon"""
    outer = list(polygon.exterior.coords)
    inners = [list(g.coords) for g in polygon.interiors]
    return outer, inners


def polyfill(
    geometry: MultiPolyOrPoly, resolution: int, geo_json: bool = False
) -> Set[str]:
    """h3.polyfill accepting a shapely (Multi)Polygon

    Parameters
    ----------
    geometry : Polygon or Multipolygon
        Polygon to fill
    resolution : int
        H3 resolution of the filling cells
    geo_json : bool
        If True, coordinates are assumed to be lng/lat. Default: False (lat/lng)

    Returns
    -------
    Set of H3 addresses

    Raises
    ------
    TypeError if geometry is not a Polygon or MultiPolygon
    """
    if isinstance(geometry, Polygon):
        outer, inners = _extract_coords(geometry)
        return h3.polyfill_polygon(outer, resolution, inners, geo_json)

    elif isinstance(geometry, MultiPolygon):
        h3_addresses = []
        for poly in geometry.geoms:
            h3_addresses.extend(polyfill(poly, resolution, geo_json))

        return set(h3_addresses)
    else:
        raise TypeError(f"Unknown type {type(geometry)}")


@sequential_deduplication
def linetrace(
    geometry: MultiLineOrLine, resolution: int
) -> Iterator[str]:
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
            a = h3.geo_to_h3(*i[::-1], resolution)
            b = h3.geo_to_h3(*j[::-1], resolution)
            yield from h3.h3_line(a, b)  # inclusive of a and b
    else:
        raise TypeError(f"Unknown type {type(geometry)}")
