def dump(poly):
    # Import special modules ...
    try:
        import shapely
        import shapely.geometry
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Check argument ...
    if not isinstance(poly, shapely.geometry.polygon.Polygon):
        raise TypeError("\"poly\" is not a Polygon")

    # Open CSV file ...
    with open("error.csv", "wt") as fobj:
        # Write header ...
        fobj.write("lon [°],lat [°]\n")

        # Loop over coordinates in external ring ...
        for lon, lat in poly.exterior.coords:
            # Write data ...
            fobj.write("{:.12f},{:.12f}\n".format(lon, lat))