from datetime import timedelta

from sqlalchemy import text

from database.connection import SessionLocal
from database.models import WeatherObservation


def calculate_weather_features(
    observations,
    current
):
    """
    Calculate time-dependent weather features
    for one weather observation.
    """

    current_time = current.timestamp

    # --------------------------------------------------------
    # Find observations within time windows
    # --------------------------------------------------------

    obs_24h = [
        obs
        for obs in observations
        if current_time - timedelta(hours=24)
        <= obs.timestamp
        <= current_time
    ]

    obs_72h = [
        obs
        for obs in observations
        if current_time - timedelta(hours=72)
        <= obs.timestamp
        <= current_time
    ]

    # --------------------------------------------------------
    # Snowfall
    # --------------------------------------------------------

    snowfall_24h = sum(
        (obs.snowfall or 0)
        for obs in obs_24h
    )

    snowfall_72h = sum(
        (obs.snowfall or 0)
        for obs in obs_72h
    )

    # --------------------------------------------------------
    # Maximum wind gust
    # --------------------------------------------------------

    gust_values = [
        obs.wind_gust
        for obs in obs_24h
        if obs.wind_gust is not None
    ]

    max_gust_24h = (
        max(gust_values)
        if gust_values
        else None
    )

    # --------------------------------------------------------
    # Temperature change over ~6 hours
    # --------------------------------------------------------

    target_time = (
        current_time -
        timedelta(hours=6)
    )

    candidates = []

    for obs in observations:

        difference = abs(
            (
                obs.timestamp -
                target_time
            ).total_seconds()
        )

        if difference <= 2 * 3600:
            candidates.append(
                (difference, obs)
            )

    temperature_change_6h = None

    if candidates:

        candidates.sort(
            key=lambda x: x[0]
        )

        previous = candidates[0][1]

        if (
            current.temperature is not None
            and previous.temperature is not None
        ):

            temperature_change_6h = (
                current.temperature -
                previous.temperature
            )

    return {
        "snowfall_24h":
            snowfall_24h,

        "snowfall_72h":
            snowfall_72h,

        "max_gust_24h":
            max_gust_24h,

        "temperature_change_6h":
            temperature_change_6h
    }


def build_features():

    db = SessionLocal()

    try:

        mountains = db.execute(
            text("""
                SELECT
                    id,
                    name
                FROM mountains
                ORDER BY id
            """)
        ).fetchall()

        print()
        print("=" * 70)
        print("8W ML FEATURE BUILDING")
        print("=" * 70)
        print(
            f"Mountains: {len(mountains)}"
        )
        print("=" * 70)

        total_created = 0

        for mountain in mountains:

            mountain_id = mountain.id
            mountain_name = mountain.name

            print()
            print(
                f"Processing: "
                f"{mountain_name}"
            )

            # ------------------------------------------------
            # Get all weather observations
            # ------------------------------------------------

            observations = (
                db.query(
                    WeatherObservation
                )
                .filter(
                    WeatherObservation.mountain_id
                    == mountain_id
                )
                .order_by(
                    WeatherObservation.timestamp
                )
                .all()
            )

            print(
                f"  Weather observations: "
                f"{len(observations)}"
            )

            if not observations:
                print(
                    "  ✗ No weather data"
                )
                continue

            # ------------------------------------------------
            # Terrain
            # ------------------------------------------------

            terrain = db.execute(
                text("""
                    SELECT
                        slope_mean,
                        slope_max,
                        elevation_min,
                        elevation_max,
                        slope_30_35_pct,
                        slope_35_40_pct,
                        slope_40_45_pct,
                        slope_above_45_pct
                    FROM terrain_features
                    WHERE mountain_id = :mountain_id
                    LIMIT 1
                """),
                {
                    "mountain_id":
                        mountain_id
                }
            ).fetchone()

            # ------------------------------------------------
            # Historical SAFE-HMA
            # ------------------------------------------------

            historical = db.execute(
                text("""
                    SELECT
                        mean_frequency,
                        max_frequency,
                        frequency_5plus_pct,
                        frequency_10plus_pct,
                        frequency_20plus_pct,
                        coverage_pct
                    FROM historical_avalanche_features
                    WHERE mountain_id = :mountain_id
                      AND radius_m = 10000
                    LIMIT 1
                """),
                {
                    "mountain_id":
                        mountain_id
                }
            ).fetchone()

            if historical is None:

                print(
                    "  ✗ No historical data"
                )

                continue

            # ------------------------------------------------
            # Build one ML row per weather observation
            # ------------------------------------------------

            created_for_mountain = 0

            for current in observations:

                weather_features = (
                    calculate_weather_features(
                        observations,
                        current
                    )
                )

                # --------------------------------------------
                # Insert / update feature row
                # --------------------------------------------

                sql = text("""
                    INSERT INTO ml_features
                    (
                        observation_id,
                        mountain_id,
                        timestamp,

                        temperature,
                        snowfall,
                        snow_depth,
                        wind_speed,
                        wind_gust,

                        snowfall_24h,
                        snowfall_72h,
                        max_gust_24h,
                        temperature_change_6h,

                        slope_mean,
                        slope_max,
                        elevation_min,
                        elevation_max,

                        slope_30_35_pct,
                        slope_35_40_pct,
                        slope_40_45_pct,
                        slope_above_45_pct,

                        historical_mean_frequency,
                        historical_max_frequency,
                        historical_5plus_pct,
                        historical_10plus_pct,
                        historical_20plus_pct,
                        historical_coverage_pct
                    )
                    VALUES
                    (
                        :observation_id,
                        :mountain_id,
                        :timestamp,

                        :temperature,
                        :snowfall,
                        :snow_depth,
                        :wind_speed,
                        :wind_gust,

                        :snowfall_24h,
                        :snowfall_72h,
                        :max_gust_24h,
                        :temperature_change_6h,

                        :slope_mean,
                        :slope_max,
                        :elevation_min,
                        :elevation_max,

                        :slope_30_35_pct,
                        :slope_35_40_pct,
                        :slope_40_45_pct,
                        :slope_above_45_pct,

                        :historical_mean_frequency,
                        :historical_max_frequency,
                        :historical_5plus_pct,
                        :historical_10plus_pct,
                        :historical_20plus_pct,
                        :historical_coverage_pct
                    )

                    ON DUPLICATE KEY UPDATE

                        timestamp =
                            VALUES(timestamp),

                        temperature =
                            VALUES(temperature),

                        snowfall =
                            VALUES(snowfall),

                        snow_depth =
                            VALUES(snow_depth),

                        wind_speed =
                            VALUES(wind_speed),

                        wind_gust =
                            VALUES(wind_gust),

                        snowfall_24h =
                            VALUES(snowfall_24h),

                        snowfall_72h =
                            VALUES(snowfall_72h),

                        max_gust_24h =
                            VALUES(max_gust_24h),

                        temperature_change_6h =
                            VALUES(temperature_change_6h)
                """)

                db.execute(
                    sql,
                    {
                        "observation_id":
                            current.id,

                        "mountain_id":
                            mountain_id,

                        "timestamp":
                            current.timestamp,

                        "temperature":
                            current.temperature,

                        "snowfall":
                            current.snowfall,

                        "snow_depth":
                            current.snow_depth,

                        "wind_speed":
                            current.wind_speed,

                        "wind_gust":
                            current.wind_gust,

                        "snowfall_24h":
                            weather_features[
                                "snowfall_24h"
                            ],

                        "snowfall_72h":
                            weather_features[
                                "snowfall_72h"
                            ],

                        "max_gust_24h":
                            weather_features[
                                "max_gust_24h"
                            ],

                        "temperature_change_6h":
                            weather_features[
                                "temperature_change_6h"
                            ],

                        "slope_mean":
                            terrain.slope_mean
                            if terrain
                            else None,

                        "slope_max":
                            terrain.slope_max
                            if terrain
                            else None,

                        "elevation_min":
                            terrain.elevation_min
                            if terrain
                            else None,

                        "elevation_max":
                            terrain.elevation_max
                            if terrain
                            else None,

                        "slope_30_35_pct":
                            terrain.slope_30_35_pct
                            if terrain
                            else None,

                        "slope_35_40_pct":
                            terrain.slope_35_40_pct
                            if terrain
                            else None,

                        "slope_40_45_pct":
                            terrain.slope_40_45_pct
                            if terrain
                            else None,

                        "slope_above_45_pct":
                            terrain.slope_above_45_pct
                            if terrain
                            else None,

                        "historical_mean_frequency":
                            historical.mean_frequency,

                        "historical_max_frequency":
                            historical.max_frequency,

                        "historical_5plus_pct":
                            historical.frequency_5plus_pct,

                        "historical_10plus_pct":
                            historical.frequency_10plus_pct,

                        "historical_20plus_pct":
                            historical.frequency_20plus_pct,

                        "historical_coverage_pct":
                            historical.coverage_pct
                    }
                )

                created_for_mountain += 1

            db.commit()

            total_created += (
                created_for_mountain
            )

            print(
                f"  ✓ ML features created: "
                f"{created_for_mountain}"
            )

        print()
        print("=" * 70)
        print("ML FEATURE BUILD COMPLETE")
        print("=" * 70)
        print(
            f"Total feature rows: "
            f"{total_created}"
        )
        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":
    build_features()