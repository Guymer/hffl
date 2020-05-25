def loadGeoJSON(fname):
    # Import special modules ...
    try:
        import geojson
        geojson.geometry.Geometry.__init__.__defaults__ = (None, False, 12)     # NOTE: https://github.com/jazzband/geojson/issues/135#issuecomment-596509669
    except:
        raise Exception("run \"pip install --user geojson\"")
    try:
        import shapely
        import shapely.ops
    except:
        raise Exception("run \"pip install --user shapely\"")

    # Load GeoJSON ...
    data = geojson.load(open(fname, "rt"))

    # Decide what to do ...
    if data["type"] == "Polygon":
        # Make list containing single Polygon ...
        polys1 = [data["coordinates"]]
    elif data["type"] == "MultiPolygon":
        # Make list containing all Polygons ...
        polys1 = data["coordinates"]
    else:
        raise Exception("geometry not supported")

    # Initialize list ...
    polys2 = []

    # Loop over polygons ...
    for poly1 in polys1:
        # Initialize lists ...
        exteriorRing = []
        interiorRings = []

        # Loop over coordinates in external ring ...
        for lon, lat in poly1[0]:
            # Check that the coordinates are not duplicated ...
            if (lon, lat) not in exteriorRing:
                # Append coordinates to list ...
                exteriorRing.append((lon, lat))

        # Skip this polygon if the external ring is not atleast a triangle ...
        if len(exteriorRing) <= 2:
            continue

        # Convert external ring to LinearRing and skip if it is not valid ...
        exteriorRing = shapely.geometry.polygon.LinearRing(exteriorRing)
        if not exteriorRing.is_valid:
            continue

        # Check if there are any interior rings ...
        if len(poly1) > 1:
            # Loop over interior rings ...
            for ring in poly1[1:]:
                # Initialize list ...
                interiorRing = []

                # Loop over coordinates in interior ring ...
                for lon, lat in ring:
                    # Check that the coordinates are not duplicated ...
                    if (lon, lat) not in interiorRing:
                        # Append coordinates to list ...
                        interiorRing.append((lon, lat))

                # Skip this interior ring if it is not atleast a triangle ...
                if len(interiorRing) <= 2:
                    continue

                # Convert interior ring to LinearRing and skip if it is not
                # valid ...
                interiorRing = shapely.geometry.polygon.LinearRing(interiorRing)
                if not interiorRing.is_valid:
                    continue

                # Append interior ring to list ...
                interiorRings.append(interiorRing)

        # Make Polygon and skip if it is not valid ...
        poly2 = shapely.geometry.polygon.Polygon(exteriorRing, interiorRings)
        if not poly2.is_valid:
            continue

        # Append Polygon to list ...
        polys2.append(poly2)

    # Make MulitPolygon ...
    multipoly = shapely.geometry.multipolygon.MultiPolygon(polys2)
    if not multipoly.is_valid:
        raise Exception("\"multipoly\" is not a valid [Multi]Polygon")

    # Return answer ...
    return multipoly
