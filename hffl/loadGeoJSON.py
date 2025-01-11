#!/usr/bin/env python3

# Define function ...
def loadGeoJSON(
    fname,
    /,
    *,
    onlyValid = False,
       repair = False,
):
    # Import special modules ...
    try:
        import geojson
        geojson.geometry.Geometry.__init__.__defaults__ = (None, False, 12)     # NOTE: See https://github.com/jazzband/geojson/issues/135#issuecomment-596509669
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
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

    # Load the GeoJSON shape(s) and convert it to a Shapely shape(s) ...
    with open(fname, "rt", encoding = "utf-8") as fObj:
        shapes = geojson.load(fObj)
    shapes = shapely.geometry.shape(shapes)

    # Initialize list ...
    polys2 = []

    # Loop over Polygons ...
    for poly1 in pyguymer3.geo.extract_polys(
        shapes,
        onlyValid = onlyValid,
           repair = repair,
    ):
        # Initialize lists ...
        exteriorRing = []
        interiorRings = []

        # Loop over coordinates in exterior ring ...
        for lon, lat in poly1.exterior.coords:
            # Check that the coordinates are not duplicated ...
            if (lon, lat) not in exteriorRing:
                # Append coordinates to list ...
                exteriorRing.append((lon, lat))

        # Skip this polygon if the exterior ring is not atleast a triangle ...
        if len(exteriorRing) <= 2:
            continue

        # Convert exterior ring to LinearRing and skip if it is not valid or is
        # empty ...
        exteriorRing = shapely.geometry.polygon.LinearRing(exteriorRing)
        if not exteriorRing.is_valid:
            print(f"WARNING: Skipping an exterior ring as it is not valid ({shapely.validation.explain_validity(exteriorRing)}).")
            continue
        if exteriorRing.is_empty:
            continue

        # Check if there are any interior rings ...
        if len(poly1.interiors) > 1:
            # Loop over interior rings ...
            for ring in poly1.interiors:
                # Initialize list ...
                interiorRing = []

                # Loop over coordinates in interior ring ...
                for lon, lat in ring.coords:
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
                if not interiorRing.is_valid:
                    print(f"WARNING: Skipping an interior ring as it is not valid ({shapely.validation.explain_validity(interiorRing)}).")
                    continue
                if interiorRing.is_empty:
                    continue

                # Append interior ring to list ...
                interiorRings.append(interiorRing)

        # Make Polygon and skip if it is not valid or is empty ...
        poly2 = shapely.geometry.polygon.Polygon(exteriorRing, interiorRings)
        if not poly2.is_valid:
            print(f"WARNING: Skipping a polygon as it is not valid ({shapely.validation.explain_validity(poly2)}).")
            continue
        if poly2.is_empty:
            continue

        # Append Polygon to list ...
        polys2.append(poly2)

    # Make [Multi]Polygon ...
    multipoly = shapely.ops.unary_union(polys2)
    pyguymer3.geo.check(multipoly)

    # Return answer ...
    return multipoly
