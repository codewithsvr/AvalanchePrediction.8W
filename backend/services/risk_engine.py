from sqlalchemy import text

from database.connection import SessionLocal


# ============================================================
# 8W RISK ENGINE V2
# ============================================================
#
# Weather contribution: 70%
# Terrain contribution: 30%
#
# This is a research prototype.
# It is NOT a certified avalanche forecast.
# ============================================================


def calculate_weather_score(features):
    """
    Calculate the existing weather-based risk score.

    Maximum weather score = 100.
    """

    current = features.get("current", {})
    weather = features.get("features", {})

    score = 0
    contributors = []

    # --------------------------------------------------------
    # 1. Snowfall - 24 hours
    # --------------------------------------------------------

    snowfall_24h = float(
        weather.get("snowfall_24h", 0) or 0
    )

    if snowfall_24h >= 30:
        snow_score = 35
        severity = "HIGH"

    elif snowfall_24h >= 20:
        snow_score = 25
        severity = "ELEVATED"

    elif snowfall_24h >= 10:
        snow_score = 15
        severity = "MODERATE"

    elif snowfall_24h >= 5:
        snow_score = 8
        severity = "LOW"

    else:
        snow_score = 0
        severity = "MINIMAL"

    score += snow_score

    contributors.append({
        "factor": "24H SNOWFALL",
        "value": f"{snowfall_24h:.2f} cm",
        "severity": severity
    })

    # --------------------------------------------------------
    # 2. Snowfall - 72 hours
    # --------------------------------------------------------

    snowfall_72h = float(
        weather.get("snowfall_72h", 0) or 0
    )

    if snowfall_72h >= 50:
        snow72_score = 15
        severity = "HIGH"

    elif snowfall_72h >= 25:
        snow72_score = 8
        severity = "ELEVATED"

    else:
        snow72_score = 0
        severity = "MINIMAL"

    score += snow72_score

    contributors.append({
        "factor": "72H SNOWFALL",
        "value": f"{snowfall_72h:.2f} cm",
        "severity": severity
    })

    # --------------------------------------------------------
    # 3. Wind speed
    # --------------------------------------------------------

    wind_speed = float(
        current.get("wind_speed", 0) or 0
    )

    if wind_speed >= 60:
        wind_score = 15
        severity = "HIGH"

    elif wind_speed >= 40:
        wind_score = 10
        severity = "ELEVATED"

    elif wind_speed >= 25:
        wind_score = 5
        severity = "MODERATE"

    else:
        wind_score = 0
        severity = "MINIMAL"

    score += wind_score

    contributors.append({
        "factor": "WIND SPEED",
        "value": f"{wind_speed:.1f} km/h",
        "severity": severity
    })

    # --------------------------------------------------------
    # 4. Wind gust
    # --------------------------------------------------------

    wind_gust = float(
        current.get("wind_gust", 0) or 0
    )

    if wind_gust >= 80:
        gust_score = 15
        severity = "HIGH"

    elif wind_gust >= 60:
        gust_score = 10
        severity = "ELEVATED"

    elif wind_gust >= 40:
        gust_score = 5
        severity = "MODERATE"

    else:
        gust_score = 0
        severity = "MINIMAL"

    score += gust_score

    contributors.append({
        "factor": "WIND GUST",
        "value": f"{wind_gust:.1f} km/h",
        "severity": severity
    })

    # --------------------------------------------------------
    # 5. Temperature change - 6 hours
    # --------------------------------------------------------

    temperature_change_6h = weather.get(
        "temperature_change_6h"
    )

    if temperature_change_6h is not None:

        temperature_change_6h = float(
            temperature_change_6h
        )

        absolute_change = abs(
            temperature_change_6h
        )

        if absolute_change >= 8:
            temp_score = 20
            severity = "HIGH"

        elif absolute_change >= 4:
            temp_score = 10
            severity = "MODERATE"

        else:
            temp_score = 0
            severity = "MINIMAL"

        score += temp_score

        contributors.append({
            "factor": "6H TEMPERATURE CHANGE",
            "value": f"{temperature_change_6h:+.1f}°C",
            "severity": severity
        })

    # --------------------------------------------------------
    # 6. Snow depth
    # --------------------------------------------------------

    snow_depth = float(
        current.get("snow_depth", 0) or 0
    )

    if snow_depth >= 1.5:
        depth_score = 15
        severity = "HIGH"

    elif snow_depth >= 1.0:
        depth_score = 10
        severity = "ELEVATED"

    elif snow_depth >= 0.5:
        depth_score = 5
        severity = "MODERATE"

    else:
        depth_score = 0
        severity = "MINIMAL"

    score += depth_score

    contributors.append({
        "factor": "SNOW DEPTH",
        "value": f"{snow_depth:.2f} m",
        "severity": severity
    })

    return {
        "score": min(score, 100),
        "contributors": contributors
    }


# ============================================================
# TERRAIN DATA
# ============================================================

def get_terrain_features(mountain_id):
    """
    Fetch terrain features from MySQL.
    """

    db = SessionLocal()

    try:
        query = text("""
            SELECT
                mountain_id,
                slope_mean,
                slope_max,
                aspect_mean,
                elevation_min,
                elevation_max,
                slope_below_25_pct,
                slope_25_30_pct,
                slope_30_35_pct,
                slope_35_40_pct,
                slope_40_45_pct,
                slope_above_45_pct
            FROM terrain_features
            WHERE mountain_id = :mountain_id
            LIMIT 1
        """)

        result = db.execute(
            query,
            {
                "mountain_id": mountain_id
            }
        ).mappings().first()

        if result is None:
            return None

        return dict(result)

    finally:
        db.close()


# ============================================================
# TERRAIN SCORE
# ============================================================

def calculate_terrain_score(terrain):
    """
    Calculate terrain exposure score.

    Maximum terrain score = 75.
    """

    if terrain is None:
        return {
            "score": 0,
            "normalized_score": 0,
            "contributors": [],
            "available": False
        }

    score = 0
    contributors = []

    # --------------------------------------------------------
    # 1. 30-45 degree terrain
    # --------------------------------------------------------

    slope_30_35 = float(
        terrain.get("slope_30_35_pct", 0) or 0
    )

    slope_35_40 = float(
        terrain.get("slope_35_40_pct", 0) or 0
    )

    slope_40_45 = float(
        terrain.get("slope_40_45_pct", 0) or 0
    )

    relevant_slope_pct = (
        slope_30_35 +
        slope_35_40 +
        slope_40_45
    )

    if relevant_slope_pct >= 35:
        slope_score = 30
        severity = "HIGH"

    elif relevant_slope_pct >= 25:
        slope_score = 22
        severity = "ELEVATED"

    elif relevant_slope_pct >= 15:
        slope_score = 12
        severity = "MODERATE"

    elif relevant_slope_pct >= 5:
        slope_score = 5
        severity = "LOW"

    else:
        slope_score = 0
        severity = "MINIMAL"

    score += slope_score

    contributors.append({
        "factor": "30–45° TERRAIN",
        "value": f"{relevant_slope_pct:.2f}%",
        "severity": severity
    })

    # --------------------------------------------------------
    # 2. Terrain above 45 degrees
    # --------------------------------------------------------

    slope_above_45 = float(
        terrain.get("slope_above_45_pct", 0) or 0
    )

    if slope_above_45 >= 35:
        steep_score = 20
        severity = "HIGH"

    elif slope_above_45 >= 25:
        steep_score = 15
        severity = "ELEVATED"

    elif slope_above_45 >= 15:
        steep_score = 10
        severity = "MODERATE"

    elif slope_above_45 >= 5:
        steep_score = 5
        severity = "LOW"

    else:
        steep_score = 0
        severity = "MINIMAL"

    score += steep_score

    contributors.append({
        "factor": ">45° TERRAIN",
        "value": f"{slope_above_45:.2f}%",
        "severity": severity
    })

    # --------------------------------------------------------
    # 3. Mean slope
    # --------------------------------------------------------

    slope_mean = float(
        terrain.get("slope_mean", 0) or 0
    )

    if slope_mean >= 40:
        mean_score = 15
        severity = "HIGH"

    elif slope_mean >= 35:
        mean_score = 12
        severity = "ELEVATED"

    elif slope_mean >= 30:
        mean_score = 8
        severity = "MODERATE"

    elif slope_mean >= 25:
        mean_score = 4
        severity = "LOW"

    else:
        mean_score = 0
        severity = "MINIMAL"

    score += mean_score

    contributors.append({
        "factor": "MEAN SLOPE",
        "value": f"{slope_mean:.2f}°",
        "severity": severity
    })

    # --------------------------------------------------------
    # 4. Elevation range
    # --------------------------------------------------------

    elevation_min = float(
        terrain.get("elevation_min", 0) or 0
    )

    elevation_max = float(
        terrain.get("elevation_max", 0) or 0
    )

    elevation_range = (
        elevation_max -
        elevation_min
    )

    if elevation_range >= 4000:
        elevation_score = 10
        severity = "HIGH"

    elif elevation_range >= 3000:
        elevation_score = 7
        severity = "ELEVATED"

    elif elevation_range >= 2000:
        elevation_score = 4
        severity = "MODERATE"

    else:
        elevation_score = 0
        severity = "LOW"

    score += elevation_score

    contributors.append({
        "factor": "ELEVATION RANGE",
        "value": f"{elevation_range:.0f} m",
        "severity": severity
    })

    score = min(score, 75)

    normalized_score = (
        score / 75
    ) * 100

    return {
        "score": score,
        "normalized_score": round(
            normalized_score,
            2
        ),
        "contributors": contributors,
        "available": True
    }


# ============================================================
# FINAL RISK ENGINE V2
# ============================================================

def calculate_risk(features):

    mountain_id = features.get(
        "mountain_id"
    )

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    weather_result = calculate_weather_score(
        features
    )

    weather_score = weather_result["score"]

    # --------------------------------------------------------
    # Terrain
    # --------------------------------------------------------

    terrain = get_terrain_features(
        mountain_id
    )

    terrain_result = calculate_terrain_score(
        terrain
    )

    terrain_score = terrain_result[
        "normalized_score"
    ]

    # --------------------------------------------------------
    # Combined score
    # --------------------------------------------------------

    if terrain_result["available"]:

        final_score = (
            weather_score * 0.70
            +
            terrain_score * 0.30
        )

    else:

        # If terrain is unavailable,
        # don't silently pretend it exists.
        final_score = weather_score

    final_score = round(
        min(max(final_score, 0), 100),
        2
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    if final_score < 20:
        risk_level = "LOW"

    elif final_score < 40:
        risk_level = "GUARDED"

    elif final_score < 60:
        risk_level = "MODERATE"

    elif final_score < 80:
        risk_level = "HIGH"

    else:
        risk_level = "VERY HIGH"

    # --------------------------------------------------------
    # Combine contributors
    # --------------------------------------------------------

    contributors = []

    # Weather contributors
    for contributor in weather_result[
        "contributors"
    ]:
        contributors.append(contributor)

    # Terrain contributors
    for contributor in terrain_result[
        "contributors"
    ]:
        contributors.append(contributor)

    # --------------------------------------------------------
    # Data quality
    # --------------------------------------------------------

    observations_available = features.get(
        "observations_available",
        0
    )

    if observations_available >= 72:
        data_quality = 100

    elif observations_available >= 48:
        data_quality = 85

    elif observations_available >= 24:
        data_quality = 70

    elif observations_available >= 12:
        data_quality = 50

    elif observations_available >= 6:
        data_quality = 30

    else:
        data_quality = 15

    # --------------------------------------------------------
    # Weather coverage confidence
    # --------------------------------------------------------

    if observations_available >= 72:
        coverage_score = 100

    elif observations_available >= 48:
        coverage_score = 80

    elif observations_available >= 24:
        coverage_score = 60

    elif observations_available >= 12:
        coverage_score = 40

    else:
        coverage_score = 20

    # --------------------------------------------------------
    # Feature availability
    # --------------------------------------------------------

    important_features = [
        "snowfall_24h",
        "snowfall_72h",
        "temperature_change_6h",
        "wind_speed",
        "wind_gust",
        "snow_depth"
    ]

    available_features = 0

    weather_feature_data = features.get(
        "features",
        {}
    )

    current_data = features.get(
        "current",
        {}
    )

    if weather_feature_data.get(
        "snowfall_24h"
    ) is not None:
        available_features += 1

    if weather_feature_data.get(
        "snowfall_72h"
    ) is not None:
        available_features += 1

    if weather_feature_data.get(
        "temperature_change_6h"
    ) is not None:
        available_features += 1

    if current_data.get(
        "wind_speed"
    ) is not None:
        available_features += 1

    if current_data.get(
        "wind_gust"
    ) is not None:
        available_features += 1

    if current_data.get(
        "snow_depth"
    ) is not None:
        available_features += 1

    feature_score = (
        available_features /
        len(important_features)
    ) * 100

    weather_confidence = round(
        coverage_score * 0.6
        +
        feature_score * 0.4
    )

    # Terrain is static DEM-derived data,
    # so it gets full availability confidence
    # when a record exists.
    terrain_confidence = (
        100
        if terrain_result["available"]
        else 0
    )

    confidence = round(
        weather_confidence * 0.70
        +
        terrain_confidence * 0.30
    )

    confidence = min(
        max(confidence, 0),
        100
    )

    return {
        "risk_index": final_score,
        "risk_level": risk_level,

        "weather_score": round(
            weather_score,
            2
        ),

        "terrain_score": round(
            terrain_score,
            2
        ),

        "weather_weight": 0.70,
        "terrain_weight": 0.30,

        "confidence": confidence,

        "data_quality": data_quality,

        "terrain_available":
            terrain_result["available"],

        "contributors": contributors
    }