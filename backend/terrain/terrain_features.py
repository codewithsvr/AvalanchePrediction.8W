import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling
)


def get_utm_crs(latitude, longitude):
    """
    Return the appropriate UTM CRS.
    """

    zone = int((longitude + 180) / 6) + 1

    if latitude >= 0:
        epsg = 32600 + zone
    else:
        epsg = 32700 + zone

    return f"EPSG:{epsg}"


def calculate_terrain_features(
    dem_path,
    latitude,
    longitude
):
    """
    Calculate terrain features from a DEM.
    """

    dem_path = Path(dem_path)

    with rasterio.open(dem_path) as src:

        target_crs = get_utm_crs(
            latitude,
            longitude
        )

        transform, width, height = calculate_default_transform(
            src.crs,
            target_crs,
            src.width,
            src.height,
            *src.bounds
        )

        elevation = np.full(
            (height, width),
            np.nan,
            dtype=np.float32
        )

        reproject(
            source=rasterio.band(src, 1),
            destination=elevation,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=target_crs,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear
        )

    # ---------------------------------------------------------
    # Pixel dimensions in meters
    # ---------------------------------------------------------

    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)

    # ---------------------------------------------------------
    # Elevation gradients
    # ---------------------------------------------------------

    dz_dy, dz_dx = np.gradient(
        elevation,
        pixel_height,
        pixel_width
    )

    # ---------------------------------------------------------
    # Slope in degrees
    # ---------------------------------------------------------

    slope = np.degrees(
        np.arctan(
            np.sqrt(
                dz_dx ** 2 +
                dz_dy ** 2
            )
        )
    )

    # ---------------------------------------------------------
    # Aspect
    # ---------------------------------------------------------

    aspect = np.degrees(
        np.arctan2(
            dz_dx,
            -dz_dy
        )
    )

    aspect = (aspect + 360) % 360

    # ---------------------------------------------------------
    # Valid pixels
    # ---------------------------------------------------------

    valid = np.isfinite(elevation)
    valid &= np.isfinite(slope)
    valid &= slope >= 0
    valid &= slope <= 90

    if not np.any(valid):
        raise ValueError(
            "No valid terrain pixels found"
        )

    valid_elevation = elevation[valid]
    valid_slope = slope[valid]
    valid_aspect = aspect[valid]

    total_pixels = len(valid_slope)

    # ---------------------------------------------------------
    # Slope distribution
    # ---------------------------------------------------------

    below_25 = np.sum(valid_slope < 25)

    slope_25_30 = np.sum(
        (valid_slope >= 25) &
        (valid_slope < 30)
    )

    slope_30_35 = np.sum(
        (valid_slope >= 30) &
        (valid_slope < 35)
    )

    slope_35_40 = np.sum(
        (valid_slope >= 35) &
        (valid_slope < 40)
    )

    slope_40_45 = np.sum(
        (valid_slope >= 40) &
        (valid_slope <= 45)
    )

    above_45 = np.sum(
        valid_slope > 45
    )

    # Convert counts → percentages

    slope_below_25_pct = (
        below_25 / total_pixels
    ) * 100

    slope_25_30_pct = (
        slope_25_30 / total_pixels
    ) * 100

    slope_30_35_pct = (
        slope_30_35 / total_pixels
    ) * 100

    slope_35_40_pct = (
        slope_35_40 / total_pixels
    ) * 100

    slope_40_45_pct = (
        slope_40_45 / total_pixels
    ) * 100

    slope_above_45_pct = (
        above_45 / total_pixels
    ) * 100

    # ---------------------------------------------------------
    # Circular mean aspect
    # ---------------------------------------------------------

    aspect_radians = np.radians(
        valid_aspect
    )

    mean_sin = np.mean(
        np.sin(aspect_radians)
    )

    mean_cos = np.mean(
        np.cos(aspect_radians)
    )

    aspect_mean = (
        math.degrees(
            math.atan2(
                mean_sin,
                mean_cos
            )
        )
        + 360
    ) % 360

    # ---------------------------------------------------------
    # Return features
    # ---------------------------------------------------------

    return {

        "slope_mean": round(
            float(np.mean(valid_slope)),
            2
        ),

        "slope_max": round(
            float(np.max(valid_slope)),
            2
        ),

        "aspect_mean": round(
            float(aspect_mean),
            2
        ),

        "elevation_min": round(
            float(np.min(valid_elevation)),
            2
        ),

        "elevation_max": round(
            float(np.max(valid_elevation)),
            2
        ),

        "slope_below_25_pct": round(
            float(slope_below_25_pct),
            2
        ),

        "slope_25_30_pct": round(
            float(slope_25_30_pct),
            2
        ),

        "slope_30_35_pct": round(
            float(slope_30_35_pct),
            2
        ),

        "slope_35_40_pct": round(
            float(slope_35_40_pct),
            2
        ),

        "slope_40_45_pct": round(
            float(slope_40_45_pct),
            2
        ),

        "slope_above_45_pct": round(
            float(slope_above_45_pct),
            2
        ),

        "pixels_analyzed": int(
            total_pixels
        ),

        "crs_used": target_crs
    }