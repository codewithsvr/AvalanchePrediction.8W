def calculate_terrain_risk(terrain):
    """
    Calculate a terrain exposure score from DEM-derived
    terrain characteristics.

    This is a research prototype, not an avalanche forecast.
    """

    if terrain is None:
        return {
            "terrain_score": 0,
            "terrain_level": "UNKNOWN",
            "contributors": []
        }

    score = 0
    contributors = []

    # ---------------------------------------------------------
    # 1. Terrain in the 30–45° range
    # ---------------------------------------------------------
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

    # More terrain in this range means greater
    # exposure to potentially avalanche-relevant slopes.
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

    # ---------------------------------------------------------
    # 2. Very steep terrain
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 3. Mean slope
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 4. Elevation range
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Maximum terrain score
    # ---------------------------------------------------------
    score = min(score, 75)

    # ---------------------------------------------------------
    # Terrain level
    # ---------------------------------------------------------
    if score < 15:
        level = "LOW"

    elif score < 30:
        level = "GUARDED"

    elif score < 45:
        level = "MODERATE"

    elif score < 60:
        level = "HIGH"

    else:
        level = "VERY HIGH"

    return {
        "terrain_score": score,
        "terrain_level": level,
        "contributors": contributors
    }