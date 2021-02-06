# How Far From Land (HFFL)

This project aims to show how far away you are from National Trust or Open Access land.

## Dependencies

HFFL requires the following Python modules to be installed and available in your `PYTHONPATH`.

* [cartopy](https://pypi.org/project/Cartopy/)
* [geojson](https://pypi.org/project/geojson/)
* [matplotlib](https://pypi.org/project/matplotlib/)
* [PIL](https://pypi.org/project/Pillow/)
* [pyguymer3](https://github.com/Guymer/PyGuymer3)
* [shapefile](https://pypi.org/project/pyshp/)
* [shapely](https://pypi.org/project/Shapely/)

## Bugs

* The GeoJSON files that the script saves (to save time the next time it is run) are not reversible. When a GeoJSON is written, each of the Polygons that makes up the MultiPolygon has already been checked to make sure that it is valid (according to the `.is_valid` Shapely value). However, upon loading the GeoJSON some of the Polygons that make up the MultiPolygon are now invalid (again, according to the `.is_valid` Shapely value). I suspect that this is a loss of precision issue, but I might be wrong.
