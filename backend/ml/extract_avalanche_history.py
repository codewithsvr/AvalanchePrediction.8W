from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform

from database.connection import SessionLocal
from database.models import Mountain


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "safe_hma"

RASTERS = {
    "Ganga_Brahmaputra":
        DATA_DIR /
        "SAFE_HMA_33ys_1990_2023_Ganga_Brahmaputra.tif",

    "Indus":
        DATA_DIR /
        "SAFE_HMA_33ys_1990_2023_Indus.tif"
}

RADIUS_M = 10000


# ============================================================
# COORDINATE TRANSFORMATION
# ============================================================

def transform_coordinates(
    latitude,
    longitude,
    target_crs
):
    """
    Convert mountain coordinates from WGS84
    (latitude/longitude) to raster CRS.
    """

    x, y = transform(
        "EPSG:4326",
        target_crs,
        [longitude],
        [latitude]
    )

    return x[0], y[0]


# ============================================================
# EXTRACT LOCAL RASTER
# ============================================================

def extract_raster_features(
    raster_path,
    latitude,
    longitude,
    radius_m
):

    with rasterio.open(raster_path) as src:

        # ----------------------------------------------------
        # Transform mountain coordinates
        # ----------------------------------------------------

        x, y = transform_coordinates(
            latitude,
            longitude,
            src.crs
        )

        # ----------------------------------------------------
        # Check whether coordinate is inside raster
        # ----------------------------------------------------

        if not (
            src.bounds.left <= x <= src.bounds.right
            and
            src.bounds.bottom <= y <= src.bounds.top
        ):
            return None

        # ----------------------------------------------------
        # Convert coordinate to raster row/column
        # ----------------------------------------------------

        row, col = src.index(x, y)

        # ----------------------------------------------------
        # Convert radius from metres to pixels
        # ----------------------------------------------------

        pixel_width = abs(src.res[0])
        pixel_height = abs(src.res[1])

        radius_x = int(
            np.ceil(radius_m / pixel_width)
        )

        radius_y = int(
            np.ceil(radius_m / pixel_height)
        )

        # ----------------------------------------------------
        # Create square window around mountain
        # ----------------------------------------------------

        window = Window(
            col - radius_x,
            row - radius_y,
            radius_x * 2 + 1,
            radius_y * 2 + 1
        )

        # Keep window inside raster
        window = window.intersection(
            Window(
                0,
                0,
                src.width,
                src.height
            )
        )

        # ----------------------------------------------------
        # Read raster data
        # ----------------------------------------------------

        data = src.read(
            1,
            window=window
        )

        # ----------------------------------------------------
        # Create circular mask
        # ----------------------------------------------------

        rows, cols = np.indices(
            data.shape
        )

        global_rows = (
            rows + window.row_off
        )

        global_cols = (
            cols + window.col_off
        )

        distance_x = (
            global_cols - col
        ) * pixel_width

        distance_y = (
            global_rows - row
        ) * pixel_height

        distance_squared = (
            distance_x ** 2
            +
            distance_y ** 2
        )

        circular_mask = (
            distance_squared
            <= radius_m ** 2
        )

        selected_pixels = data[
            circular_mask
        ]

        total_pixels = len(
            selected_pixels
        )

        # ----------------------------------------------------
        # SAFE-HMA uses 0 as NoData
        # ----------------------------------------------------

        valid_pixels = selected_pixels[
            selected_pixels > 0
        ]

        valid_count = len(
            valid_pixels
        )

        if valid_count == 0:
            return {
                "total_pixels": total_pixels,
                "valid_pixels": 0,
                "coverage_pct": 0.0,
                "mean_frequency": None,
                "max_frequency": None,
                "frequency_5plus_pct": None,
                "frequency_10plus_pct": None,
                "frequency_20plus_pct": None
            }

        # ----------------------------------------------------
        # Historical avalanche statistics
        # ----------------------------------------------------

        mean_frequency = float(
            np.mean(valid_pixels)
        )

        max_frequency = int(
            np.max(valid_pixels)
        )

        frequency_5plus_pct = float(
            np.mean(
                valid_pixels >= 5
            ) * 100
        )

        frequency_10plus_pct = float(
            np.mean(
                valid_pixels >= 10
            ) * 100
        )

        frequency_20plus_pct = float(
            np.mean(
                valid_pixels >= 20
            ) * 100
        )

        coverage_pct = (
            valid_count /
            total_pixels
        ) * 100

        return {
            "total_pixels": total_pixels,
            "valid_pixels": valid_count,
            "coverage_pct": coverage_pct,
            "mean_frequency": mean_frequency,
            "max_frequency": max_frequency,
            "frequency_5plus_pct":
                frequency_5plus_pct,
            "frequency_10plus_pct":
                frequency_10plus_pct,
            "frequency_20plus_pct":
                frequency_20plus_pct
        }


# ============================================================
# FIND BEST BASIN
# ============================================================

def extract_mountain_history(
    mountain
):

    candidates = []

    for basin, raster_path in RASTERS.items():

        if not raster_path.exists():

            print(
                f"  ✗ Missing raster: "
                f"{raster_path.name}"
            )

            continue

        try:

            features = extract_raster_features(
                raster_path,
                mountain.latitude,
                mountain.longitude,
                RADIUS_M
            )

            if features is None:
                continue

            candidates.append(
                (
                    basin,
                    features,
                    raster_path
                )
            )

        except Exception as error:

            print(
                f"  ✗ Error reading "
                f"{basin}: {repr(error)}"
            )

    if not candidates:
        return None

    # --------------------------------------------------------
    # If both rasters contain the coordinate,
    # choose the one with greater valid coverage.
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item:
        item[1]["valid_pixels"],
        reverse=True
    )

    return candidates[0]


# ============================================================
# SAVE TO MYSQL
# ============================================================

def save_features(
    db,
    mountain,
    basin,
    features,
    raster_path
):

    sql = """
        INSERT INTO historical_avalanche_features
        (
            mountain_id,
            basin,
            radius_m,
            total_pixels,
            valid_pixels,
            coverage_pct,
            mean_frequency,
            max_frequency,
            frequency_5plus_pct,
            frequency_10plus_pct,
            frequency_20plus_pct,
            source
        )
        VALUES
        (
            :mountain_id,
            :basin,
            :radius_m,
            :total_pixels,
            :valid_pixels,
            :coverage_pct,
            :mean_frequency,
            :max_frequency,
            :frequency_5plus_pct,
            :frequency_10plus_pct,
            :frequency_20plus_pct,
            :source
        )
        ON DUPLICATE KEY UPDATE

            basin = VALUES(basin),
            total_pixels = VALUES(total_pixels),
            valid_pixels = VALUES(valid_pixels),
            coverage_pct = VALUES(coverage_pct),
            mean_frequency = VALUES(mean_frequency),
            max_frequency = VALUES(max_frequency),
            frequency_5plus_pct =
                VALUES(frequency_5plus_pct),
            frequency_10plus_pct =
                VALUES(frequency_10plus_pct),
            frequency_20plus_pct =
                VALUES(frequency_20plus_pct),
            source = VALUES(source)
    """

    from sqlalchemy import text

    db.execute(
        text(sql),
        {
            "mountain_id": mountain.id,
            "basin": basin,
            "radius_m": RADIUS_M,
            "total_pixels":
                features["total_pixels"],
            "valid_pixels":
                features["valid_pixels"],
            "coverage_pct":
                features["coverage_pct"],
            "mean_frequency":
                features["mean_frequency"],
            "max_frequency":
                features["max_frequency"],
            "frequency_5plus_pct":
                features["frequency_5plus_pct"],
            "frequency_10plus_pct":
                features["frequency_10plus_pct"],
            "frequency_20plus_pct":
                features["frequency_20plus_pct"],
            "source":
                raster_path.name
        }
    )

    db.commit()


# ============================================================
# MAIN
# ============================================================

def process_all_mountains():

    db = SessionLocal()

    try:

        mountains = (
            db.query(Mountain)
            .order_by(Mountain.id)
            .all()
        )

        print()
        print("=" * 70)
        print("8W HISTORICAL AVALANCHE EXTRACTION")
        print("=" * 70)
        print(
            f"Mountains found: {len(mountains)}"
        )
        print(
            f"Analysis radius: {RADIUS_M} m"
        )
        print("=" * 70)

        successful = 0
        failed = 0

        for mountain in mountains:

            print()
            print(
                f"Processing: {mountain.name}"
            )

            print(
                f"  Coordinates: "
                f"{mountain.latitude}, "
                f"{mountain.longitude}"
            )

            try:

                result = extract_mountain_history(
                    mountain
                )

                if result is None:

                    print(
                        "  ✗ No SAFE-HMA "
                        "coverage found"
                    )

                    failed += 1
                    continue

                (
                    basin,
                    features,
                    raster_path
                ) = result

                print(
                    f"  Basin: {basin}"
                )

                print(
                    f"  Valid pixels: "
                    f"{features['valid_pixels']}"
                )

                print(
                    f"  Coverage: "
                    f"{features['coverage_pct']:.2f}%"
                )

                if features[
                    "mean_frequency"
                ] is not None:

                    print(
                        f"  Mean frequency: "
                        f"{features['mean_frequency']:.2f}"
                    )

                    print(
                        f"  Maximum frequency: "
                        f"{features['max_frequency']}"
                    )

                    print(
                        f"  ≥5 years: "
                        f"{features['frequency_5plus_pct']:.2f}%"
                    )

                    print(
                        f"  ≥10 years: "
                        f"{features['frequency_10plus_pct']:.2f}%"
                    )

                    print(
                        f"  ≥20 years: "
                        f"{features['frequency_20plus_pct']:.2f}%"
                    )

                save_features(
                    db,
                    mountain,
                    basin,
                    features,
                    raster_path
                )

                successful += 1

                print(
                    "  ✓ Historical "
                    "features saved"
                )

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"  ✗ Failed: "
                    f"{repr(error)}"
                )

        print()
        print("=" * 70)
        print("HISTORICAL EXTRACTION COMPLETE")
        print("=" * 70)
        print(
            f"Successful: {successful}"
        )
        print(
            f"Failed:     {failed}"
        )
        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":
    process_all_mountains()