from typing import Union, Set, Tuple, List
from shapely.geometry import Polygon, MultiPolygon
from h3 import h3

MultiPolyOrPoly = Union[Polygon, MultiPolygon]


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
