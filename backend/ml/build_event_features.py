from datetime import datetime, timedelta

from database.connection import SessionLocal
from database.models import (
    AvalancheEvent,
    AvalancheEventMatch,
    AvalancheEventWeather,
    TerrainFeature,
    HistoricalAvalancheFeature,
    AvalancheEventFeature
)


def build_event_features():

    db = SessionLocal()

    try:

        matches = (
            db.query(AvalancheEventMatch)
            .order_by(AvalancheEventMatch.event_date)
            .all()
        )

        print("\n8W EVENT FEATURE EXTRACTION")
        print("=" * 60)

        successful = 0
        failed = 0

        for match in matches:

            try:

                event = (
                    db.query(AvalancheEvent)
                    .filter(
                        AvalancheEvent.id ==
                        match.avalanche_event_id
                    )
                    .first()
                )

                if not event:
                    print(
                        f"✗ Event {match.avalanche_event_id} "
                        f"not found"
                    )
                    failed += 1
                    continue

                if not event.event_date:
                    print(
                        f"✗ Event {event.id} has no date"
                    )
                    failed += 1
                    continue

                mountain_id = match.mountain_id

                event_start = datetime.combine(
                    event.event_date,
                    datetime.min.time()
                )

                pre_24_start = event_start - timedelta(hours=24)
                pre_48_start = event_start - timedelta(hours=48)
                pre_72_start = event_start - timedelta(hours=72)

                weather_rows = (
                    db.query(AvalancheEventWeather)
                    .filter(
                        AvalancheEventWeather.avalanche_event_id
                        == event.id
                    )
                    .order_by(
                        AvalancheEventWeather.timestamp
                    )
                    .all()
                )

                if not weather_rows:

                    print(
                        f"✗ Event {event.id}: "
                        f"no weather data"
                    )

                    failed += 1
                    continue

                # -----------------------------------------
                # WEATHER WINDOWS
                # -----------------------------------------

                pre_24 = [
                    row for row in weather_rows
                    if pre_24_start <= row.timestamp < event_start
                ]

                pre_48 = [
                    row for row in weather_rows
                    if pre_48_start <= row.timestamp < event_start
                ]

                pre_72 = [
                    row for row in weather_rows
                    if pre_72_start <= row.timestamp < event_start
                ]

                event_day = [
                    row for row in weather_rows
                    if event_start
                    <= row.timestamp
                    < event_start + timedelta(hours=24)
                ]

                # -----------------------------------------
                # SNOWFALL
                # -----------------------------------------

                snowfall_24h = sum(
                    row.snowfall or 0
                    for row in pre_24
                )

                snowfall_48h = sum(
                    row.snowfall or 0
                    for row in pre_48
                )

                snowfall_72h = sum(
                    row.snowfall or 0
                    for row in pre_72
                )

                # -----------------------------------------
                # WIND
                # -----------------------------------------

                wind_values = [
                    row.wind_speed
                    for row in pre_24
                    if row.wind_speed is not None
                ]

                gust_values = [
                    row.wind_gust
                    for row in pre_24
                    if row.wind_gust is not None
                ]

                max_wind_24h = (
                    max(wind_values)
                    if wind_values
                    else None
                )

                max_gust_24h = (
                    max(gust_values)
                    if gust_values
                    else None
                )

                # -----------------------------------------
                # TEMPERATURE
                # -----------------------------------------

                temperature_values = [
                    row.temperature
                    for row in pre_72
                    if row.temperature is not None
                ]

                temperature_min = (
                    min(temperature_values)
                    if temperature_values
                    else None
                )

                temperature_max = (
                    max(temperature_values)
                    if temperature_values
                    else None
                )

                mean_temperature = (
                    sum(temperature_values)
                    / len(temperature_values)
                    if temperature_values
                    else None
                )

                # Compare event-day mean temperature
                # with previous 24h mean temperature.

                pre_temp_values = [
                    row.temperature
                    for row in pre_24
                    if row.temperature is not None
                ]

                event_temp_values = [
                    row.temperature
                    for row in event_day
                    if row.temperature is not None
                ]

                pre_temp_mean = (
                    sum(pre_temp_values)
                    / len(pre_temp_values)
                    if pre_temp_values
                    else None
                )

                event_temp_mean = (
                    sum(event_temp_values)
                    / len(event_temp_values)
                    if event_temp_values
                    else None
                )

                temperature_change = None

                if (
                    pre_temp_mean is not None
                    and event_temp_mean is not None
                ):
                    temperature_change = (
                        event_temp_mean
                        - pre_temp_mean
                    )

                # -----------------------------------------
                # SNOW DEPTH
                # -----------------------------------------

                snow_depth_values = [
                    row.snow_depth
                    for row in pre_72
                    if row.snow_depth is not None
                ]

                snow_depth_min = (
                    min(snow_depth_values)
                    if snow_depth_values
                    else None
                )

                snow_depth_max = (
                    max(snow_depth_values)
                    if snow_depth_values
                    else None
                )

                pre_depth_values = [
                    row.snow_depth
                    for row in pre_24
                    if row.snow_depth is not None
                ]

                event_depth_values = [
                    row.snow_depth
                    for row in event_day
                    if row.snow_depth is not None
                ]

                pre_depth_mean = (
                    sum(pre_depth_values)
                    / len(pre_depth_values)
                    if pre_depth_values
                    else None
                )

                event_depth_mean = (
                    sum(event_depth_values)
                    / len(event_depth_values)
                    if event_depth_values
                    else None
                )

                snow_depth_change = None

                if (
                    pre_depth_mean is not None
                    and event_depth_mean is not None
                ):
                    snow_depth_change = (
                        event_depth_mean
                        - pre_depth_mean
                    )

                # -----------------------------------------
                # MEAN WIND
                # -----------------------------------------

                mean_wind_speed = (
                    sum(wind_values)
                    / len(wind_values)
                    if wind_values
                    else None
                )

                # -----------------------------------------
                # TERRAIN
                # -----------------------------------------

                terrain = (
                    db.query(TerrainFeature)
                    .filter(
                        TerrainFeature.mountain_id
                        == mountain_id
                    )
                    .first()
                )

                slope_mean = None
                slope_above_45_pct = None
                elevation_range = None

                if terrain:

                    slope_mean = terrain.slope_mean

                    slope_above_45_pct = (
                        terrain.slope_above_45_pct
                    )

                    if (
                        terrain.elevation_min is not None
                        and terrain.elevation_max is not None
                    ):
                        elevation_range = (
                            terrain.elevation_max
                            - terrain.elevation_min
                        )

                # -----------------------------------------
                # HISTORICAL AVALANCHE FEATURES
                # -----------------------------------------

                historical = (
                    db.query(HistoricalAvalancheFeature)
                    .filter(
                        HistoricalAvalancheFeature.mountain_id
                        == mountain_id,
                        HistoricalAvalancheFeature.radius_m
                        == 10000
                    )
                    .first()
                )

                historical_mean_frequency = None
                historical_max_frequency = None
                historical_5plus_pct = None
                historical_10plus_pct = None
                historical_20plus_pct = None
                historical_coverage_pct = None

                if historical:

                    historical_mean_frequency = (
                        historical.mean_frequency
                    )

                    historical_max_frequency = (
                        historical.max_frequency
                    )

                    historical_5plus_pct = (
                        historical.frequency_5plus_pct
                    )

                    historical_10plus_pct = (
                        historical.frequency_10plus_pct
                    )

                    historical_20plus_pct = (
                        historical.frequency_20plus_pct
                    )

                    historical_coverage_pct = (
                        historical.coverage_pct
                    )

                # -----------------------------------------
                # MATCH TYPE
                # -----------------------------------------

                match_type = (
                    "LOCAL"
                    if match.distance_km <= 25
                    else "REGIONAL"
                )

                # -----------------------------------------
                # UPSERT
                # -----------------------------------------

                existing = (
                    db.query(AvalancheEventFeature)
                    .filter(
                        AvalancheEventFeature.avalanche_event_id
                        == event.id
                    )
                    .first()
                )

                if existing:

                    feature = existing

                else:

                    feature = AvalancheEventFeature(
                        avalanche_event_id=event.id,
                        mountain_id=mountain_id
                    )

                    db.add(feature)

                feature.event_date = event.event_date
                feature.distance_km = match.distance_km
                feature.match_type = match_type

                feature.snowfall_24h = snowfall_24h
                feature.snowfall_48h = snowfall_48h
                feature.snowfall_72h = snowfall_72h

                feature.max_wind_24h = max_wind_24h
                feature.max_gust_24h = max_gust_24h

                feature.temperature_min = temperature_min
                feature.temperature_max = temperature_max
                feature.mean_temperature = mean_temperature
                feature.temperature_change = temperature_change

                feature.snow_depth_min = snow_depth_min
                feature.snow_depth_max = snow_depth_max
                feature.snow_depth_change = snow_depth_change

                feature.mean_wind_speed = mean_wind_speed

                feature.slope_mean = slope_mean
                feature.slope_above_45_pct = slope_above_45_pct
                feature.elevation_range = elevation_range

                feature.historical_mean_frequency = (
                    historical_mean_frequency
                )

                feature.historical_max_frequency = (
                    historical_max_frequency
                )

                feature.historical_5plus_pct = (
                    historical_5plus_pct
                )

                feature.historical_10plus_pct = (
                    historical_10plus_pct
                )

                feature.historical_20plus_pct = (
                    historical_20plus_pct
                )

                feature.historical_coverage_pct = (
                    historical_coverage_pct
                )

                feature.label = 1

                db.commit()

                successful += 1

                print(
                    f"✓ Event {event.id} | "
                    f"{event.location} | "
                    f"{event.event_date} | "
                    f"{match_type} | "
                    f"{match.distance_km:.2f} km"
                )

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"✗ Event {match.avalanche_event_id}: "
                    f"{repr(error)}"
                )

        print("=" * 60)
        print(
            f"Completed: {successful} successful, "
            f"{failed} failed"
        )


    finally:
        db.close()


if __name__ == "__main__":
    build_event_features()