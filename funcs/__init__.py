# Import standard modules ...
import sys

# Import sub-functions ...
from .dump import dump
from .loadGeoJSON import loadGeoJSON
from .loadShapefile import loadShapefile

# Ensure that this module is only imported by Python 3.x ...
if sys.version_info.major != 3:
    raise Exception("this Python module must only be used with Python 3.x")
