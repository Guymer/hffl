#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.10/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import io
    import json
    import os
    import zipfile

    # Import special modules ...
    try:
        import cartopy
        import cartopy.crs
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import geojson
        geojson.geometry.Geometry.__init__.__defaults__ = (None, False, 12)     # NOTE: https://github.com/jazzband/geojson/issues/135#issuecomment-596509669
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
    try:
        import matplotlib
        matplotlib.use("Agg")                                                   # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
        import matplotlib.pyplot
    except:
        raise Exception("\"matplotlib\" is not installed; run \"pip install --user matplotlib\"") from None
    try:
        import shapefile
    except:
        raise Exception("\"shapefile\" is not installed; run \"pip install --user pyshp\"") from None
    try:
        import shapely
        import shapely.ops
        import shapely.validation
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    import funcs
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
    except:
        raise Exception("\"pyguymer3\" is not installed; you need to have the Python module from https://github.com/Guymer/PyGuymer3 located somewhere in your $PYTHONPATH") from None

    # Set number of bearings and degree of simplification ...
    dpi = 300                                                                   # [px/in]
    nang = 361                                                                  # [#]
    simp = 0.0001                                                               # [°]

    # Set field-of-view and padding ...
    fov = 0.5                                                                   # [°]
    pad = 0.1                                                                   # [°]

    # Set mode and use it to override number of bearings and degree of
    # simplification (if needed) ...
    debug = False
    if debug:
        dpi = 150                                                               # [px/in]
        nang = 9                                                                # [#]
        simp = 0.1                                                              # [°]

    # Create short-hand for the colour map ...
    cmap = matplotlib.pyplot.get_cmap("jet")

    # Load tile metadata ...
    with open("OrdnanceSurveyBackgroundImages/miniscale.json", "rt", encoding = "utf-8") as fobj:
        meta = json.load(fobj)

    # **************************************************************************

    # Start session ...
    sess = pyguymer3.start_session()

    # Download dataset if it is missing ...
    fname = "alwaysOpen.zip"
    if not os.path.exists(fname):
        url = "https://opendata.arcgis.com/datasets/202ec400dfe9471aaf257e4b6c956394_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
        pyguymer3.download_file(sess, url, fname)

    # Download dataset if it is missing ...
    fname = "limitedAccess.zip"
    if not os.path.exists(fname):
        url = "https://opendata.arcgis.com/datasets/f3cd21fd165e4e3498a83973bb5ba82f_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
        pyguymer3.download_file(sess, url, fname)

    # Download dataset if it is missing ...
    fname = "openAccess.zip"
    if not os.path.exists(fname):
        url = "https://opendata.arcgis.com/datasets/6ce15f2cd06c4536983d315694dad16b_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
        pyguymer3.download_file(sess, url, fname)

    # Close session ...
    sess.close()

    # **************************************************************************

    # Define locations ...
    locs = [
        (51.268, -1.088, "Basingstoke Train Station", "basingstoke"),           # [°], [°]
        (51.459, -0.974, "Reading Train Station"    , "reading"    ),           # [°], [°]
        (53.378, -1.462, "Sheffield Train Station"  , "sheffield"  ),           # [°], [°]
        (54.779, -1.583, "Durham Train Station"     , "durham"     ),           # [°], [°]
    ]

    # Loop over locations ...
    for y, x, title, stub in locs:
        print(f"Making \"{stub}\" ...")

        # Define bounding box ...
        xmin, xmax, ymin, ymax = x - fov, x + fov, y - fov, y + fov             # [°], [°], [°], [°]

        # Deduce GeoJSON name and check what needs doing ...
        fname = f"{stub}.geojson"
        if os.path.exists(fname):
            print(f"  Loading \"{fname}\" ...")

            # Load GeoJSON ...
            multipoly = funcs.loadGeoJSON(fname)
        else:
            print(f"  Saving \"{fname}\" ...")

            # Initialize list ...
            polys = []

            # ******************************************************************

            print("    Loading \"alwaysOpen.zip\" ...")

            # Load dataset ...
            with zipfile.ZipFile("alwaysOpen.zip", "r") as zfObj:
                # Read files into RAM so that they become seekable ...
                # NOTE: https://stackoverflow.com/a/12025492
                dbfObj = io.BytesIO(zfObj.read("d00dbcdd-ca42-4b51-9889-50627184f7602020313-1-1rdxbnd.c0er.dbf"))
                shpObj = io.BytesIO(zfObj.read("d00dbcdd-ca42-4b51-9889-50627184f7602020313-1-1rdxbnd.c0er.shp"))
                shxObj = io.BytesIO(zfObj.read("d00dbcdd-ca42-4b51-9889-50627184f7602020313-1-1rdxbnd.c0er.shx"))

                # Open shapefile ...
                sfObj = shapefile.Reader(dbf = dbfObj, shp = shpObj, shx = shxObj)

                # Load all [Multi]Polygons from the shapefile ...
                polys += funcs.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

            # ******************************************************************

            print("    Loading \"limitedAccess.zip\" ...")

            # Load dataset ...
            with zipfile.ZipFile("limitedAccess.zip", "r") as zfObj:
                # Read files into RAM so that they become seekable ...
                # NOTE: https://stackoverflow.com/a/12025492
                dbfObj = io.BytesIO(zfObj.read("9a97e056-3bd9-4817-a9c5-ad7de1f31a1d2020313-1-rlrdj0.1jac.dbf"))
                shpObj = io.BytesIO(zfObj.read("9a97e056-3bd9-4817-a9c5-ad7de1f31a1d2020313-1-rlrdj0.1jac.shp"))
                shxObj = io.BytesIO(zfObj.read("9a97e056-3bd9-4817-a9c5-ad7de1f31a1d2020313-1-rlrdj0.1jac.shx"))

                # Open shapefile ...
                sfObj = shapefile.Reader(dbf = dbfObj, shp = shpObj, shx = shxObj)

                # Load all [Multi]Polygons from the shapefile ...
                polys += funcs.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

            # ******************************************************************

            print("    Loading \"openAccess.zip\" ...")

            # Load dataset ...
            with zipfile.ZipFile("openAccess.zip", "r") as zfObj:
                # Read files into RAM so that they become seekable ...
                # NOTE: https://stackoverflow.com/a/12025492
                dbfObj = io.BytesIO(zfObj.read("CRoW_Access_Land___Natural_England.dbf"))
                shpObj = io.BytesIO(zfObj.read("CRoW_Access_Land___Natural_England.shp"))
                shxObj = io.BytesIO(zfObj.read("CRoW_Access_Land___Natural_England.shx"))

                # Open shapefile ...
                sfObj = shapefile.Reader(dbf = dbfObj, shp = shpObj, shx = shxObj)

                # Load all [Multi]Polygons from the shapefile ...
                polys += funcs.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

            # ******************************************************************

            print("    Unifying data ...")

            # Convert list of [Multi]Polygons to (unified) [Multi]Polygon ...
            multipoly = shapely.ops.unary_union(polys)

            # Check [Multi]Polygon ...
            if not multipoly.is_valid:
                raise Exception(f"\"multipoly\" is not a valid [Multi]Polygon ({shapely.validation.explain_validity(multipoly)})") from None

            # Check [Multi]Polygon ...
            if multipoly.is_empty:
                raise Exception("\"multipoly\" is an empty [Multi]Polygon") from None

            # Save GeoJSON ...
            with open(fname, "wt", encoding = "utf-8") as fobj:
                geojson.dump(
                    multipoly,
                    fobj,
                    ensure_ascii = False,
                          indent = 4,
                       sort_keys = True,
                )

        # **********************************************************************

        print("  Buffering data ...")

        # Initialize float ...
        dist = 0.0                                                              # [m]

        # Loop over distances ...
        for i in range(6):
            # Increment distance ...
            dist += 500.0                                                       # [m]

            # Deduce GeoJSON name and check what needs doing ...
            fname = f"{stub}{dist:04.0f}m.geojson"
            if os.path.exists(fname):
                print(f"    Buffering for {0.001 * dist:.1f} km (loading \"{fname}\") ...")

                # Load GeoJSON ...
                multipoly = funcs.loadGeoJSON(fname)
            else:
                print(f"    Buffering for {0.001 * dist:.1f} km (saving \"{fname}\") ...")

                # Buffer MultiPolygon ...
                multipoly = pyguymer3.geo.buffer(multipoly, 500.0, debug = debug, nang = nang, simp = simp)

                # Save GeoJSON ...
                with open(fname, "wt", encoding = "utf-8") as fobj:
                    geojson.dump(
                        multipoly,
                        fobj,
                        ensure_ascii = False,
                              indent = 4,
                           sort_keys = True,
                    )

    # NOTE: I break the loop here and do it again so that all of the GeoJSON
    #       file are made before any of the PNGs are made. This is because there
    #       is a bug in how "multiprocessing" works on newer versions of Mac OS
    #       X. This bug can be triggered in this script due to the use of
    #       "multiprocessing" in conjunction with "matplotlib". See:
    #         * https://github.com/matplotlib/matplotlib/issues/15410
    #         * https://bugs.python.org/issue33725

    # Loop over locations ...
    for y, x, title, stub in locs:
        print(f"Making \"{stub}\" ...")

        # Define bounding box ...
        xmin, xmax, ymin, ymax = x - fov, x + fov, y - fov, y + fov             # [°], [°], [°], [°]

        print("  Plotting data ...")

        # Create figure ...
        fg = matplotlib.pyplot.figure(figsize = (9, 6), dpi = dpi)
        ax = fg.add_subplot(projection = cartopy.crs.PlateCarree())
        ax.set_extent([xmin, xmax, ymin, ymax])
        ax.set_title(f"Distance From NT & OA Land ({title})")
        if debug:
            ax.coastlines(resolution = "110m", color = "black", linewidth = 0.1)
        else:
            ax.coastlines(resolution = "10m", color = "black", linewidth = 0.1)

        # Deduce GeoJSON name ...
        fname = f"{stub}.geojson"

        # Load GeoJSON ...
        multipoly = funcs.loadGeoJSON(fname)

        # Draw data ...
        ax.add_geometries(
            multipoly,
            cartopy.crs.PlateCarree(),
            alpha = 1.0,
            edgecolor = "none",
            facecolor = "red",
        )

        # Initialize float and lists ...
        dist = 0.0                                                              # [m]
        labels = []
        lines = []

        # Loop over distances ...
        for i in range(6):
            # Increment distance ...
            dist += 500.0                                                       # [m]

            # Deduce GeoJSON name ...
            fname = f"{stub}{dist:04.0f}m.geojson"

            # Load GeoJSON ...
            multipoly = funcs.loadGeoJSON(fname)

            # Draw data ...
            if isinstance(multipoly, shapely.geometry.polygon.Polygon):
                ax.add_geometries(
                    [multipoly],
                    cartopy.crs.PlateCarree(),
                    alpha = 1.0,
                    edgecolor = cmap(float(i) / 5.0),
                    facecolor = "none",
                    linewidth = 1.0
                )
            elif isinstance(multipoly, shapely.geometry.multipolygon.MultiPolygon):
                ax.add_geometries(
                    multipoly,
                    cartopy.crs.PlateCarree(),
                    alpha = 1.0,
                    edgecolor = cmap(float(i) / 5.0),
                    facecolor = "none",
                    linewidth = 1.0
                )
            else:
                raise TypeError("\"multipoly\" is not a [Multi]Polygon")

            # Add entries for the legend ...
            labels.append(f"{0.001 * dist:.1f} km")
            lines.append(matplotlib.lines.Line2D([], [], color = cmap(float(i) / 5.0)))

        # Draw background image ...
        ax.imshow(
            matplotlib.pyplot.imread(f'OrdnanceSurveyBackgroundImages/{meta["MiniScale_(mono)_R22"]["greyscale"]}'),
                     cmap = "gray",
                   extent = meta["MiniScale_(relief1)_R22"]["extent"],
            interpolation = "bicubic",
                   origin = "upper",
                transform = cartopy.crs.OSGB(),
                     vmin = 0.0,
                     vmax = 1.0,
        )

        # Add legend and save figure ...
        ax.legend(lines, labels, bbox_to_anchor = (1.0, 0.5), fontsize = "small", ncol = 1)
        fg.savefig(f"{stub}.png", bbox_inches = "tight", dpi = dpi, pad_inches = 0.1)
        if not debug:
            pyguymer3.image.optimize_image(f"{stub}.png", strip = True)
        matplotlib.pyplot.close(fg)

        # Stop looping if debugging ...
        if debug:
            break
