import asyncio
from datetime import datetime, date, timedelta

import requests
from sqlalchemy import text

from database.connection import SessionLocal


START_DATE = "1990-01-01"
END_DATE = "2023-12-31"


API_URL = "https://archive-api.open-meteo.com/v1/archive"


HOURLY_VARIABLES = (
    "temperature_2m,"
    "snowfall,"
    "snow_depth,"
    "wind_speed_10m,"
    "wind_gusts_10m"
)


def fetch_historical_weather(
    latitude,
    longitude,
    start_date,
    end_date
):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": start_date,
        "end_date": end_date,

        "hourly": HOURLY_VARIABLES,

        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",

        "timezone": "GMT",

        "models": "era5"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    return response.json()


def save_weather(
    db,
    mountain_id,
    data
):

    hourly = data.get("hourly")

    if not hourly:
        return 0

    times = hourly.get("time", [])

    temperatures = hourly.get(
        "temperature_2m",
        []
    )

    snowfall = hourly.get(
        "snowfall",
        []
    )

    snow_depth = hourly.get(
        "snow_depth",
        []
    )

    wind_speed = hourly.get(
        "wind_speed_10m",
        []
    )

    wind_gust = hourly.get(
        "wind_gusts_10m",
        []
    )

    inserted = 0

    sql = text("""
        INSERT INTO historical_weather
        (
            mountain_id,
            timestamp,
            temperature,
            snowfall,
            snow_depth,
            wind_speed,
            wind_gust,
            source
        )
        VALUES
        (
            :mountain_id,
            :timestamp,
            :temperature,
            :snowfall,
            :snow_depth,
            :wind_speed,
            :wind_gust,
            :source
        )
        ON DUPLICATE KEY UPDATE

            temperature = VALUES(temperature),
            snowfall = VALUES(snowfall),
            snow_depth = VALUES(snow_depth),
            wind_speed = VALUES(wind_speed),
            wind_gust = VALUES(wind_gust)
    """)

    for i, timestamp_string in enumerate(times):

        timestamp = datetime.fromisoformat(
            timestamp_string
        )

        db.execute(
            sql,
            {
                "mountain_id":
                    mountain_id,

                "timestamp":
                    timestamp,

                "temperature":
                    temperatures[i]
                    if i < len(temperatures)
                    else None,

                "snowfall":
                    snowfall[i]
                    if i < len(snowfall)
                    else None,

                "snow_depth":
                    snow_depth[i]
                    if i < len(snow_depth)
                    else None,

                "wind_speed":
                    wind_speed[i]
                    if i < len(wind_speed)
                    else None,

                "wind_gust":
                    wind_gust[i]
                    if i < len(wind_gust)
                    else None,

                "source":
                    "Open-Meteo ERA5"
            }
        )

        inserted += 1

    db.commit()

    return inserted


async def collect_historical_weather():

    db = SessionLocal()

    try:

        mountains = db.execute(
            text("""
                SELECT
                    id,
                    name,
                    latitude,
                    longitude
                FROM mountains
                ORDER BY id
            """)
        ).fetchall()

        print()
        print("=" * 70)
        print("8W HISTORICAL WEATHER COLLECTION")
        print("=" * 70)

        print(
            f"Period: "
            f"{START_DATE} → {END_DATE}"
        )

        print(
            f"Mountains: "
            f"{len(mountains)}"
        )

        print("=" * 70)

        total_rows = 0

        for mountain in mountains:

            print()
            print(
                f"Processing: "
                f"{mountain.name}"
            )

            print(
                f"  Coordinates: "
                f"{mountain.latitude}, "
                f"{mountain.longitude}"
            )

            try:

                data = fetch_historical_weather(
                    mountain.latitude,
                    mountain.longitude,
                    START_DATE,
                    END_DATE
                )

                count = save_weather(
                    db,
                    mountain.id,
                    data
                )

                total_rows += count

                print(
                    f"  ✓ Saved: "
                    f"{count} hourly observations"
                )

            except Exception as error:

                db.rollback()

                print(
                    f"  ✗ Failed: "
                    f"{repr(error)}"
                )

        print()
        print("=" * 70)
        print("HISTORICAL WEATHER COLLECTION COMPLETE")
        print("=" * 70)

        print(
            f"Total rows: {total_rows}"
        )

        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":

    asyncio.run(
        collect_historical_weather()
    )