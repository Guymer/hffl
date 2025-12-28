#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import io
    import json
    import os
    import pathlib
    import zipfile

    # Import special modules ...
    try:
        import cartopy
        cartopy.config.update(
            {
                "cache_dir" : pathlib.PosixPath("~/.local/share/cartopy").expanduser(),
            }
        )
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import geojson
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
    try:
        import matplotlib
        matplotlib.rcParams.update(
            {
                            "backend" : "Agg",                                  # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
                         "figure.dpi" : 300,
                     "figure.figsize" : (9.6, 7.2),                             # NOTE: See https://github.com/Guymer/misc/blob/main/README.md#matplotlib-figure-sizes
                          "font.size" : 8,
                "image.interpolation" : "none",
                     "image.resample" : False,
            }
        )
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
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    import hffl
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "HFFL: this project aims to show how far away you are from National Trust or Open Access land.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action = "store_true",
          help = "print debug messages",
    )
    parser.add_argument(
        "--timeout",
        default = 60.0,
           help = "the timeout for any requests/subprocess calls (in seconds)",
           type = float,
    )
    args = parser.parse_args()

    # **************************************************************************

    # Set number of bearings and degree of simplification ...
    nAng = 361                                                                  # [#]
    res = "10m"
    simp = 0.0001                                                               # [°]

    # Set padding and region-of-interest ...
    pad = 0.1                                                                   # [°]
    roi = 0.5                                                                   # [°]

    # Use mode to override number of bearings and degree of simplification (if
    # needed) ...
    if args.debug:
        nAng = 9                                                                # [#]
        res = "110m"
        simp = 0.1                                                              # [°]

    # Create short-hand for the colour map ...
    cmap = matplotlib.colormaps["turbo"]

    # Load tile metadata ...
    with open("OrdnanceSurveyBackgroundImages/miniscale.json", "rt", encoding = "utf-8") as fObj:
        meta = json.load(fObj)

    # **************************************************************************

    # Start session ...
    with pyguymer3.start_session() as sess:
        # Download dataset if it is missing ...
        fname = "alwaysOpen.zip"
        if not os.path.exists(fname):
            url = "https://opendata.arcgis.com/datasets/202ec400dfe9471aaf257e4b6c956394_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
            pyguymer3.download_file(
                sess,
                url,
                fname,
                  debug = args.debug,
                timeout = args.timeout,
            )

        # Download dataset if it is missing ...
        fname = "limitedAccess.zip"
        if not os.path.exists(fname):
            url = "https://opendata.arcgis.com/datasets/f3cd21fd165e4e3498a83973bb5ba82f_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
            pyguymer3.download_file(
                sess,
                url,
                fname,
                  debug = args.debug,
                timeout = args.timeout,
            )

        # Download dataset if it is missing ...
        fname = "openAccess.zip"
        if not os.path.exists(fname):
            url = "https://opendata.arcgis.com/datasets/6ce15f2cd06c4536983d315694dad16b_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
            pyguymer3.download_file(
                sess,
                url,
                fname,
                  debug = args.debug,
                timeout = args.timeout,
            )

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
        xmin, xmax, ymin, ymax = x - roi, x + roi, y - roi, y + roi             # [°], [°], [°], [°]

        # Deduce GeoJSON name and check what needs doing ...
        fname = f"{stub}.geojson"
        if os.path.exists(fname):
            print(f"  Loading \"{fname}\" ...")

            # Load GeoJSON ...
            multipoly = hffl.loadGeoJSON(
                fname,
                    debug = args.debug,
                onlyValid = True,
                   repair = True,
            )
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
                polys += hffl.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

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
                polys += hffl.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

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
                polys += hffl.loadShapefile(sfObj, xmin, xmax, ymin, ymax, pad, simp = simp)

            # ******************************************************************

            print("    Unifying data ...")

            # Convert list of [Multi]Polygons to (unified) [Multi]Polygon ...
            multipoly = shapely.ops.unary_union(polys)
            pyguymer3.geo.check(multipoly)

            # Save GeoJSON ...
            with open(fname, "wt", encoding = "utf-8") as fObj:
                geojson.dump(
                    multipoly,
                    fObj,
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
                multipoly = hffl.loadGeoJSON(
                    fname,
                        debug = args.debug,
                    onlyValid = True,
                       repair = True,
                )
            else:
                print(f"    Buffering for {0.001 * dist:.1f} km (saving \"{fname}\") ...")

                # Buffer MultiPolygon ...
                multipoly = pyguymer3.geo.buffer(
                    multipoly,
                    500.0,
                    debug = args.debug,
                     nAng = nAng,
                     simp = simp,
                )

                # Save GeoJSON ...
                with open(fname, "wt", encoding = "utf-8") as fObj:
                    geojson.dump(
                        multipoly,
                        fObj,
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

        print("  Buffering point ...")

        # Buffer Point ...
        fovPoly = pyguymer3.geo.buffer(
            shapely.geometry.point.Point(x, y),
            30.0e3,
            debug = args.debug,
             nAng = nAng,
             simp = simp,
        )

        print("  Plotting data ...")

        # Create figure ...
        fg = matplotlib.pyplot.figure(figsize = (7.2, 7.2))

        # Create axis ...
        ax = pyguymer3.geo.add_axis(
            fg,
            add_coastlines = False,
             add_gridlines = False,
                     debug = args.debug,
                      dist = 30.0e3,
                       fov = fovPoly,
                       lat = y,
                       lon = x,
        )

        # Deduce GeoJSON name ...
        fname = f"{stub}.geojson"

        # Load GeoJSON ...
        multipoly = hffl.loadGeoJSON(
            fname,
                debug = args.debug,
            onlyValid = True,
               repair = True,
        )

        # Extract data and buffer it by 50 metres to smooth out any kinks (it
        # appears that Cartopy has difficulty drawing some of the Polygons and
        # Cartopy just paints the entire map red - as of 20/Dec/2025, I have
        # been unable to figure out which Polygon it is) ...
        polys = pyguymer3.geo.extract_polys(
            pyguymer3.geo.buffer(
                multipoly.intersection(fovPoly),
                50.0,
                debug = args.debug,
                 nAng = nAng,
                 simp = simp,
            ),
            onlyValid = True,
               repair = True,
        )

        # Draw data ...
        ax.add_geometries(
            polys,
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
            multipoly = hffl.loadGeoJSON(
                fname,
                    debug = args.debug,
                onlyValid = True,
                   repair = True,
            )

            # Draw data ...
            ax.add_geometries(
                pyguymer3.geo.extract_polys(
                    multipoly.intersection(fovPoly),
                    onlyValid = True,
                       repair = True,
                ),
                cartopy.crs.PlateCarree(),
                    alpha = 1.0,
                edgecolor = cmap(float(i) / 5.0),
                facecolor = "none",
                linewidth = 1.0,
            )

            # Add entries for the legend ...
            labels.append(f"{0.001 * dist:.1f} km")
            lines.append(matplotlib.lines.Line2D([], [], color = cmap(float(i) / 5.0)))

        # Calculate the regrid shape based off the resolution and the size of
        # the figure, as well as a safety factor of 2 (remembering Nyquist) ...
        regrid_shape = (
            round(2.0 * fg.get_figwidth() * fg.get_dpi()),
            round(2.0 * fg.get_figheight() * fg.get_dpi()),
        )                                                                       # [px], [px]

        # Draw background image ...
        ax.imshow(
            matplotlib.pyplot.imread(f'OrdnanceSurveyBackgroundImages/{meta["MiniScale_(mono)_R22"]["greyscale"]}'),
                     cmap = "gray",
                   extent = meta["MiniScale_(relief1)_R22"]["extent"],
            interpolation = "gaussian",
                   origin = "upper",
             regrid_shape = regrid_shape,
                 resample = False,
                transform = cartopy.crs.OSGB(),
                     vmax = 1.0,
                     vmin = 0.0,
        )

        # Configure axis ...
        ax.legend(
            lines,
            labels,
             loc = "upper right",
            ncol = 1,
        )
        ax.set_title(f"Distance From NT & OA Land ({title})")

        # Configure figure ...
        fg.tight_layout()

        # Save figure ...
        fg.savefig(f"{stub}.png")
        matplotlib.pyplot.close(fg)

        # Optimize PNG ...
        pyguymer3.image.optimise_image(
            f"{stub}.png",
              debug = args.debug,
              strip = True,
            timeout = args.timeout,
        )

        # Stop looping if debugging ...
        if args.debug:
            break
