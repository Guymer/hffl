#!/usr/bin/env python3

# Define function ...
def loadShapefile(
    sfObj,
    xmin,
    xmax,
    ymin,
    ymax,
    pad,
    /,
    *,
    debug = __debug__,
     simp = 0.1,
):
    # Import special modules ...
    try:
        import shapefile
    except:
        raise Exception("\"shapefile\" is not installed; run \"pip install --user pyshp\"") from None
    try:
        import shapely
        import shapely.geometry
        import shapely.ops
        import shapely.validation
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    try:
        import pyguymer3
        import pyguymer3.geo
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # Check argument ...
    if not isinstance(sfObj, shapefile.Reader):
        raise TypeError("\"sfObj\" is not a shapefile.Reader")

    # **************************************************************************
    # *                    STEP 1: CREATE LIST OF POLYGONS                     *
    # **************************************************************************

    # Initialize counter and list ...
    n = 0                                                                       # [#]
    polys1 = []

    # Loop over shape+record pairs ...
    for shapeRecord in sfObj.iterShapeRecords():
        # Crash if this shape+record is not a shapefile polygon ...
        if shapeRecord.shape.shapeType != shapefile.POLYGON:
            raise Exception("\"shape\" is not a POLYGON") from None

        # Convert shapefile.Shape to shapely.geometry.polygon.Polygon or
        # shapely.geometry.multipolygon.MultiPolygon ...
        poly1 = shapely.geometry.shape(shapeRecord.shape)
        if not poly1.is_valid:
            print(f"WARNING: Skipping a shape as it is not valid ({shapely.validation.explain_validity(poly1)}).")
            n += 1                                                              # [#]
            continue
        if poly1.is_empty:
            n += 1                                                              # [#]
            continue

        # Check if it is a [Multi]Polygon ...
        match poly1:
            case shapely.geometry.polygon.Polygon():
                # Append to list ...
                polys1.append(poly1)
            case shapely.geometry.multipolygon.MultiPolygon():
                # Loop over Polygons ...
                for poly2 in poly1.geoms:
                    # Append to list ...
                    polys1.append(poly2)
            case _:
                # Crash
                raise TypeError(f"\"poly1\" is an unexpected type ({repr(type(poly1))})") from None

    print(f"      INFO: {n:,d} records were skipped because they were invalid")

    # **************************************************************************
    # *    STEP 2: CONVERT FROM EASTINGS/NORTHINGS TO LONGITUDES/LATITUDES     *
    # **************************************************************************

    # Initialize counter and list ...
    n = 0                                                                       # [#]
    polys2 = []

    # Loop over Polygons ...
    for poly1 in polys1:
        # Convert from Eastings/Northings to Longitudes/Latitudes ...
        poly2 = pyguymer3.geo.en2ll(
            poly1,
            debug = debug,
        )
        if poly2 is False:
            n += 1                                                              # [#]
            continue

        # Append to list ...
        polys2.append(poly2)

    print(f"      INFO: {n:,d} Polygons could not be converted from Eastings/Northings to Longitudes/Latitudes")

    # **************************************************************************
    # *                        STEP 3: SIMPLIFY RESULTS                        *
    # **************************************************************************

    # Initialize counter and list ...
    n = 0                                                                       # [#]
    polys3 = []

    # Loop over Polygons ...
    for poly2 in polys2:
        # Check that the Polygon overlaps with the field-of-view and its padding ...
        if poly2.bounds[0] <= xmax + pad and poly2.bounds[2] >= xmin - pad:
            if poly2.bounds[1] <= ymax + pad and poly2.bounds[3] >= ymin - pad:
                # Simplify Polygon ...
                poly3 = poly2.simplify(simp)
                if not poly3.is_valid:
                    print(f"WARNING: Skipping a polygon as it is not valid ({shapely.validation.explain_validity(poly3)}).")
                    n += 1                                                      # [#]
                    continue
                if poly3.is_empty:
                    n += 1                                                      # [#]
                    continue

                # Append to list ...
                polys3.append(poly3)

    print(f"      INFO: {n:,d} Polygons could not be simplified")

    # Return answer ...
    return polys3
