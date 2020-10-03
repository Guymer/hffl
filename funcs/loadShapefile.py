def loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = 0.1):
    # Import special modules ...
    try:
        import shapefile
    except:
        raise Exception("run \"pip install --user pyshp\"")
    try:
        import shapely
        import shapely.ops
    except:
        raise Exception("run \"pip install --user shapely\"")

    # Import my modules ...
    try:
        import pyguymer3
    except:
        raise Exception("you need to have the Python module from https://github.com/Guymer/PyGuymer3 located somewhere in your $PYTHONPATH")

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
            raise Exception("\"shape\" is not a POLYGON")

        # Convert shapefile.Shape to shapely.geometry.polygon.Polygon or
        # shapely.geometry.multipolygon.MultiPolygon ...
        poly1 = shapely.geometry.shape(shapeRecord.shape)
        if not poly1.is_valid:
            n += 1                                                              # [#]
            continue

        # Check if it is a [Multi]Polygon ...
        if isinstance(poly1, shapely.geometry.polygon.Polygon):
            # Append to list ...
            polys1.append(poly1)
        elif isinstance(poly1, shapely.geometry.multipolygon.MultiPolygon):
            # Loop over Polygons ...
            for poly2 in poly1.geoms:
                # Append to list ...
                polys1.append(poly2)
        else:
            raise TypeError("\"poly1\" is not a [Multi]Polygon")

    print("      INFO: {:,d} records were skipped because they were invalid".format(n))

    # **************************************************************************
    # *    STEP 2: CONVERT FROM EASTINGS/NORTHINGS TO LONGITUDES/LATITUDES     *
    # **************************************************************************

    # Initialize counter and list ...
    n = 0                                                                       # [#]
    polys2 = []

    # Loop over Polygons ...
    for poly1 in polys1:
        # Convert from Eastings/Northings to Longitudes/Latitudes ...
        poly2 = pyguymer3.en2ll(poly1)
        if poly2 is False:
            n += 1                                                              # [#]
            continue

        # Append to list ...
        polys2.append(poly2)

    print("      INFO: {:,d} Polygons could not be converted from Eastings/Northings to Longitudes/Latitudes".format(n))

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
                    n += 1                                                      # [#]
                    continue

                # Append to list ...
                polys3.append(poly3)

    print("      INFO: {:,d} Polygons could not be simplified".format(n))

    # Return answer ...
    return polys3
