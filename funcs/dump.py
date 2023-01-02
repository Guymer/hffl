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
    with open("error.csv", "wt", encoding = "utf-8") as fObj:
        # Write header ...
        fObj.write("lon [°],lat [°]\n")

        # Loop over coordinates in external ring ...
        for lon, lat in poly.exterior.coords:
            # Write data ...
            fObj.write(f"{lon:.15e},{lat:.15e}\n")
