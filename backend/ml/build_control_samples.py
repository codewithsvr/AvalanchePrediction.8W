import random
from datetime import datetime, timedelta

from database.connection import SessionLocal

from database.models import (
    AvalancheEventFeature,
    AvalancheEvent,
    HistoricalWeather,
    TerrainFeature,
    HistoricalAvalancheFeature,
    MlControlSample
)

CONTROL_RATIO = 2


def mean(values):

    if not values:
        return None

    return sum(values) / len(values)


def build_weather_features(rows, control_start):

    pre24_start = control_start - timedelta(hours=24)
    pre48_start = control_start - timedelta(hours=48)
    pre72_start = control_start - timedelta(hours=72)

    pre24 = [
        row for row in rows
        if pre24_start <= row.timestamp < control_start
    ]

    pre48 = [
        row for row in rows
        if pre48_start <= row.timestamp < control_start
    ]

    pre72 = [
        row for row in rows
        if pre72_start <= row.timestamp < control_start
    ]

    control_day = [
        row for row in rows
        if control_start
        <= row.timestamp
        < control_start + timedelta(hours=24)
    ]

    snowfall_24h = sum(
        row.snowfall or 0
        for row in pre24
    )

    snowfall_48h = sum(
        row.snowfall or 0
        for row in pre48
    )

    snowfall_72h = sum(
        row.snowfall or 0
        for row in pre72
    )

    wind_values = [
        row.wind_speed
        for row in pre24
        if row.wind_speed is not None
    ]

    gust_values = [
        row.wind_gust
        for row in pre24
        if row.wind_gust is not None
    ]

    temperature_values = [
        row.temperature
        for row in pre72
        if row.temperature is not None
    ]

    pre_temperature = [
        row.temperature
        for row in pre24
        if row.temperature is not None
    ]

    control_temperature = [
        row.temperature
        for row in control_day
        if row.temperature is not None
    ]

    snow_depth_values = [
        row.snow_depth
        for row in pre72
        if row.snow_depth is not None
    ]

    pre_snow_depth = [
        row.snow_depth
        for row in pre24
        if row.snow_depth is not None
    ]

    control_snow_depth = [
        row.snow_depth
        for row in control_day
        if row.snow_depth is not None
    ]

    return {
        "snowfall_24h": snowfall_24h,
        "snowfall_48h": snowfall_48h,
        "snowfall_72h": snowfall_72h,

        "max_wind_24h": (
            max(wind_values)
            if wind_values
            else None
        ),

        "max_gust_24h": (
            max(gust_values)
            if gust_values
            else None
        ),

        "temperature_min": (
            min(temperature_values)
            if temperature_values
            else None
        ),

        "temperature_max": (
            max(temperature_values)
            if temperature_values
            else None
        ),

        "mean_temperature": mean(
            temperature_values
        ),

        "temperature_change": (
            mean(control_temperature)
            - mean(pre_temperature)
            if control_temperature
            and pre_temperature
            else None
        ),

        "snow_depth_min": (
            min(snow_depth_values)
            if snow_depth_values
            else None
        ),

        "snow_depth_max": (
            max(snow_depth_values)
            if snow_depth_values
            else None
        ),

        "snow_depth_change": (
            mean(control_snow_depth)
            - mean(pre_snow_depth)
            if control_snow_depth
            and pre_snow_depth
            else None
        ),

        "mean_wind_speed": mean(
            wind_values
        )
    }


def build_control_samples():

    db = SessionLocal()

    try:

        positives = (
            db.query(AvalancheEventFeature)
            .order_by(
                AvalancheEventFeature.event_date
            )
            .all()
        )

        print("\n8W CONTROL SAMPLE GENERATION")
        print("=" * 60)

        successful = 0
        skipped = 0

        for positive in positives:

            event = (
                db.query(AvalancheEvent)
                .filter(
                    AvalancheEvent.id
                    == positive.avalanche_event_id
                )
                .first()
            )

            if not event or not event.event_date:
                continue

            mountain_id = positive.mountain_id
            event_month = event.event_date.month

            # ------------------------------------------------
            # Existing avalanche dates for this mountain
            # ------------------------------------------------

            event_dates = {
                row.event_date
                for row in db.query(AvalancheEventFeature)
                .filter(
                    AvalancheEventFeature.mountain_id
                    == mountain_id
                )
                .all()
                if row.event_date
            }

            # ------------------------------------------------
            # Candidate dates from historical weather
            # ------------------------------------------------

            weather_dates = (
                db.query(HistoricalWeather.timestamp)
                .filter(
                    HistoricalWeather.mountain_id
                    == mountain_id
                )
                .order_by(
                    HistoricalWeather.timestamp
                )
                .all()
            )

            candidate_dates = set()

            for item in weather_dates:

                timestamp = item[0]

                if timestamp.month != event_month:
                    continue

                candidate_date = timestamp.date()

                # Need a complete 72h + event-day window.
                if candidate_date.year not in (
                    2020,
                    2021,
                    2022,
                    2023
                ):
                    continue

                # Don't use known avalanche dates.
                if candidate_date in event_dates:
                    continue

                # Avoid the 3-day neighborhood around events.
                too_close = False

                for event_date in event_dates:

                    if abs(
                        (candidate_date - event_date).days
                    ) <= 3:

                        too_close = True
                        break

                if too_close:
                    continue

                candidate_dates.add(candidate_date)

            candidates = list(candidate_dates)

            random.shuffle(candidates)

            selected = 0

            for candidate_date in candidates:

                if selected >= CONTROL_RATIO:
                    break

                control_start = datetime.combine(
                    candidate_date,
                    datetime.min.time()
                )

                window_start = (
                    control_start
                    - timedelta(hours=72)
                )

                window_end = (
                    control_start
                    + timedelta(hours=24)
                )

                rows = (
                    db.query(HistoricalWeather)
                    .filter(
                        HistoricalWeather.mountain_id
                        == mountain_id,

                        HistoricalWeather.timestamp
                        >= window_start,

                        HistoricalWeather.timestamp
                        < window_end
                    )
                    .order_by(
                        HistoricalWeather.timestamp
                    )
                    .all()
                )

                # Require approximately 96 hourly observations.
                if len(rows) < 90:
                    continue

                features = build_weather_features(
                    rows,
                    control_start
                )

                # --------------------------------------------
                # Terrain
                # --------------------------------------------

                terrain = (
                    db.query(TerrainFeature)
                    .filter(
                        TerrainFeature.mountain_id
                        == mountain_id
                    )
                    .first()
                )

                if not terrain:
                    continue

                elevation_range = None

                if (
                    terrain.elevation_min is not None
                    and terrain.elevation_max is not None
                ):
                    elevation_range = (
                        terrain.elevation_max
                        - terrain.elevation_min
                    )

                # --------------------------------------------
                # Historical avalanche features
                # --------------------------------------------

                historical = (
                    db.query(
                        HistoricalAvalancheFeature
                    )
                    .filter(
                        HistoricalAvalancheFeature.mountain_id
                        == mountain_id,

                        HistoricalAvalancheFeature.radius_m
                        == 10000
                    )
                    .first()
                )

                if not historical:
                    continue

                # --------------------------------------------
                # Insert control
                # --------------------------------------------

                existing = (
                    db.query(MlControlSample)
                    .filter(
                        MlControlSample.mountain_id
                        == mountain_id,

                        MlControlSample.control_date
                        == candidate_date
                    )
                    .first()
                )

                if existing:
                    continue

                control = MlControlSample(
                    mountain_id=mountain_id,
                    control_date=candidate_date,

                    snowfall_24h=features[
                        "snowfall_24h"
                    ],

                    snowfall_48h=features[
                        "snowfall_48h"
                    ],

                    snowfall_72h=features[
                        "snowfall_72h"
                    ],

                    max_wind_24h=features[
                        "max_wind_24h"
                    ],

                    max_gust_24h=features[
                        "max_gust_24h"
                    ],

                    temperature_min=features[
                        "temperature_min"
                    ],

                    temperature_max=features[
                        "temperature_max"
                    ],

                    mean_temperature=features[
                        "mean_temperature"
                    ],

                    temperature_change=features[
                        "temperature_change"
                    ],

                    snow_depth_min=features[
                        "snow_depth_min"
                    ],

                    snow_depth_max=features[
                        "snow_depth_max"
                    ],

                    snow_depth_change=features[
                        "snow_depth_change"
                    ],

                    mean_wind_speed=features[
                        "mean_wind_speed"
                    ],

                    slope_mean=terrain.slope_mean,

                    slope_above_45_pct=(
                        terrain.slope_above_45_pct
                    ),

                    elevation_range=elevation_range,

                    historical_mean_frequency=(
                        historical.mean_frequency
                    ),

                    historical_max_frequency=(
                        historical.max_frequency
                    ),

                    historical_5plus_pct=(
                        historical.frequency_5plus_pct
                    ),

                    historical_10plus_pct=(
                        historical.frequency_10plus_pct
                    ),

                    historical_20plus_pct=(
                        historical.frequency_20plus_pct
                    ),

                    historical_coverage_pct=(
                        historical.coverage_pct
                    ),

                    matched_positive_event_id=(
                        positive.avalanche_event_id
                    ),

                    label=0
                )

                db.add(control)
                db.commit()

                successful += 1
                selected += 1

                print(
                    f"✓ Control {candidate_date} | "
                    f"Mountain {mountain_id} | "
                    f"For event "
                    f"{positive.avalanche_event_id}"
                )

        print("=" * 60)
        print(
            f"Controls created: {successful}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    build_control_samples()