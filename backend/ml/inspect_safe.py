import glob
import os

import rasterio


files = glob.glob("ml/data/safe_hma/*.tif")

for path in files:
    print("\n" + "=" * 60)
    print("FILE:", os.path.basename(path))
    print("=" * 60)

    with rasterio.open(path) as src:

        print("CRS:", src.crs)
        print(
            "Size:",
            src.width,
            "x",
            src.height
        )
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        print("Bands:", src.count)
        print("NoData:", src.nodata)

        arr = src.read(
            1,
            masked=True
        )

        print(
            "Min:",
            float(arr.min())
        )

        print(
            "Max:",
            float(arr.max())
        )

        print(
            "Mean:",
            float(arr.mean())
        )

        print(
            "Valid pixels:",
            arr.count()
        )