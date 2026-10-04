from pathlib import Path
import math
import requests


BASE_DIR = Path(__file__).resolve().parent
DEM_DIR = BASE_DIR / "data"

DEM_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def get_srtm_tile(
    latitude: float,
    longitude: float
):
    """
    Convert latitude/longitude to the
    corresponding 1-degree SRTM tile name.
    """

    lat_floor = math.floor(latitude)
    lon_floor = math.floor(longitude)

    lat_prefix = "N" if lat_floor >= 0 else "S"
    lon_prefix = "E" if lon_floor >= 0 else "W"

    return (
        f"{lat_prefix}{abs(lat_floor):02d}"
        f"{lon_prefix}{abs(lon_floor):03d}"
    )


def get_dem_path(tile_name: str):

    return DEM_DIR / f"{tile_name}.tif"


def get_tile_coordinates(
    latitude: float,
    longitude: float,
    zoom: int = 12
):
    """
    Convert latitude/longitude to Web Mercator
    tile coordinates.
    """

    n = 2 ** zoom

    x = int(
        (
            longitude + 180
        ) / 360 * n
    )

    latitude_rad = math.radians(
        latitude
    )

    y = int(
        (
            1
            -
            math.asinh(
                math.tan(latitude_rad)
            ) / math.pi
        )
        / 2
        * n
    )

    return zoom, x, y


def download_geotiff(
    latitude: float,
    longitude: float
):

    zoom, x, y = get_tile_coordinates(
        latitude,
        longitude
    )

    filename = (
        f"{zoom}_{x}_{y}.tif"
    )

    output_path = DEM_DIR / filename

    if output_path.exists():

        print(
            f"  ✓ DEM already exists: "
            f"{filename}"
        )

        return output_path

    url = (
        "https://s3.amazonaws.com/"
        "elevation-tiles-prod/"
        f"geotiff/{zoom}/{x}/{y}.tif"
    )

    print(
        f"  Downloading DEM: "
        f"{zoom}/{x}/{y}"
    )

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

    output_path.write_bytes(
        response.content
    )

    print(
        f"  ✓ Saved: {filename}"
    )

    return output_path