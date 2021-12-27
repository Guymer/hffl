def loadGeoJSON(fname):
    # Import special modules ...
    try:
        import geojson
        geojson.geometry.Geometry.__init__.__defaults__ = (None, False, 12)     # NOTE: https://github.com/jazzband/geojson/issues/135#issuecomment-596509669
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
    try:
        import shapely
        import shapely.ops
        import shapely.validation
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Load GeoJSON ...
    with open(fname, "rt", encoding = "utf-8") as fobj:
        data = geojson.load(fobj)

    # Decide what to do ...
    if data["type"] == "Polygon":
        # Make list containing single Polygon ...
        polys1 = [data["coordinates"]]
    elif data["type"] == "MultiPolygon":
        # Make list containing all Polygons ...
        polys1 = data["coordinates"]
    else:
        raise Exception("geometry not supported") from None

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

        # Convert external ring to LinearRing and skip if it is not valid or is
        # empty ...
        exteriorRing = shapely.geometry.polygon.LinearRing(exteriorRing)
        if not exteriorRing.is_valid or exteriorRing.is_empty:
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
                # valid or is empty ...
                interiorRing = shapely.geometry.polygon.LinearRing(interiorRing)
                if not interiorRing.is_valid or interiorRing.is_empty:
                    continue

                # Append interior ring to list ...
                interiorRings.append(interiorRing)

        # Make Polygon and skip if it is not valid or is empty ...
        poly2 = shapely.geometry.polygon.Polygon(exteriorRing, interiorRings)
        if not poly2.is_valid or poly2.is_empty:
            continue

        # Append Polygon to list ...
        polys2.append(poly2)

    # Make [Multi]Polygon ...
    multipoly = shapely.geometry.multipolygon.MultiPolygon(polys2)

    # Check [Multi]Polygon ...
    if not multipoly.is_valid:
        raise Exception(f"\"multipoly\" is not a valid [Multi]Polygon ({shapely.validation.explain_validity(multipoly)})") from None

    # Check [Multi]Polygon ...
    if multipoly.is_empty:
        raise Exception("\"multipoly\" is an empty [Multi]Polygon") from None

    # Return answer ...
    return multipoly
