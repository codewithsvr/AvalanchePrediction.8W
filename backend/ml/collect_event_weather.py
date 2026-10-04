from pathlib import Path
from datetime import timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sqlalchemy import text
from database.connection import SessionLocal


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

HOURS_BEFORE_EVENT = 72


# ============================================================
# FETCH WEATHER
# ============================================================

def fetch_event_weather(
    latitude,
    longitude,
    event_date
):

    start_date = (
        event_date
        - timedelta(days=3)
    )

    end_date = event_date

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date":
            start_date.isoformat(),

        "end_date":
            end_date.isoformat(),

        "hourly":
            (
                "temperature_2m,"
                "snowfall,"
                "snow_depth,"
                "wind_speed_10m,"
                "wind_gusts_10m"
            ),

        "temperature_unit":
            "celsius",

        "wind_speed_unit":
            "kmh",

        "precipitation_unit":
            "mm",

        "timezone":
            "GMT",

        "models":
            "era5"
    }

    # --------------------------------------------------------
    # Automatic retry configuration
    # --------------------------------------------------------

    retry_strategy = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=2,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ],

        allowed_methods=[
            "GET"
        ],

        raise_on_status=False
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy
    )

    session = requests.Session()

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    # --------------------------------------------------------
    # Request
    # --------------------------------------------------------

    response = session.get(
        API_URL,
        params=params,
        timeout=180
    )

    response.raise_for_status()

    return response.json()
# ============================================================
# SAVE EVENT WEATHER
# ============================================================

def save_event_weather(
    db,
    event_id,
    mountain_id,
    data
):

    hourly = data.get(
        "hourly"
    )

    if not hourly:

        return 0

    times = hourly.get(
        "time",
        []
    )

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

    sql = text("""
        INSERT INTO avalanche_event_weather
        (
            avalanche_event_id,
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
            :event_id,
            :mountain_id,
            :timestamp,

            :temperature,
            :snowfall,
            :snow_depth,
            :wind_speed,
            :wind_gust,

            'Open-Meteo ERA5'
        )

        ON DUPLICATE KEY UPDATE

            temperature =
                VALUES(temperature),

            snowfall =
                VALUES(snowfall),

            snow_depth =
                VALUES(snow_depth),

            wind_speed =
                VALUES(wind_speed),

            wind_gust =
                VALUES(wind_gust)
    """)

    saved = 0

    for i, timestamp_string in enumerate(
        times
    ):

        try:

            from datetime import datetime

            timestamp = (
                datetime.fromisoformat(
                    timestamp_string
                )
            )

            db.execute(
                sql,
                {
                    "event_id":
                        event_id,

                    "mountain_id":
                        mountain_id,

                    "timestamp":
                        timestamp,

                    "temperature":
                        (
                            temperatures[i]
                            if i < len(temperatures)
                            else None
                        ),

                    "snowfall":
                        (
                            snowfall[i]
                            if i < len(snowfall)
                            else None
                        ),

                    "snow_depth":
                        (
                            snow_depth[i]
                            if i < len(snow_depth)
                            else None
                        ),

                    "wind_speed":
                        (
                            wind_speed[i]
                            if i < len(wind_speed)
                            else None
                        ),

                    "wind_gust":
                        (
                            wind_gust[i]
                            if i < len(wind_gust)
                            else None
                        )
                }
            )

            saved += 1

        except Exception as error:

            print(
                f"    Failed timestamp "
                f"{timestamp_string}: "
                f"{repr(error)}"
            )

    return saved


# ============================================================
# MAIN
# ============================================================

def collect_event_weather():

    db = SessionLocal()

    try:

        print()
        print("=" * 70)
        print("8W AVALANCHE EVENT WEATHER COLLECTION")
        print("=" * 70)

        # ----------------------------------------------------
        # Get matched events
        # ----------------------------------------------------

        events = db.execute(
            text("""
                SELECT

                    aem.avalanche_event_id,
                    aem.mountain_id,
                    aem.distance_km,

                    ae.location,
                    ae.event_date,
                    ae.latitude,
                    ae.longitude

                FROM avalanche_event_matches aem

                JOIN avalanche_events ae
                    ON ae.id =
                       aem.avalanche_event_id

                WHERE ae.event_date IS NOT NULL
                  AND ae.latitude IS NOT NULL
                  AND ae.longitude IS NOT NULL

                ORDER BY ae.event_date
            """)
        ).fetchall()

        print(
            f"Events to process: "
            f"{len(events)}"
        )

        print(
            "Weather window: "
            "72 hours before event "
            "+ event day"
        )

        print("=" * 70)

        total_rows = 0
        successful_events = 0
        failed_events = 0

        # ----------------------------------------------------
        # Process events
        # ----------------------------------------------------

        for index, event in enumerate(
            events,
            start=1
        ):

            print()
            print(
                f"[{index}/{len(events)}] "
                f"{event.location}"
            )

            print(
                f"  Date: "
                f"{event.event_date}"
            )

            print(
                f"  Mountain ID: "
                f"{event.mountain_id}"
            )

            print(
                f"  Distance: "
                f"{event.distance_km:.2f} km"
            )

            try:

                data = fetch_event_weather(
                    event.latitude,
                    event.longitude,
                    event.event_date
                )

                saved = save_event_weather(
                    db,

                    event.avalanche_event_id,

                    event.mountain_id,

                    data
                )

                db.commit()

                total_rows += saved
                successful_events += 1

                print(
                    f"  ✓ Saved "
                    f"{saved} hourly observations"
                )

            except Exception as error:

                db.rollback()

                failed_events += 1

                print(
                    f"  ✗ Failed: "
                    f"{repr(error)}"
                )

        # ----------------------------------------------------
        # Final report
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("EVENT WEATHER COLLECTION COMPLETE")
        print("=" * 70)

        print(
            f"Successful events: "
            f"{successful_events}"
        )

        print(
            f"Failed events: "
            f"{failed_events}"
        )

        print(
            f"Weather rows saved: "
            f"{total_rows}"
        )

        print("=" * 70)

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    collect_event_weather()