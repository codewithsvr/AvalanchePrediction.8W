def calculate_risk(weather):

    current = weather.get("current", {})

    temperature = current.get(
        "temperature_2m", 0
    )

    snowfall = current.get(
        "snowfall", 0
    )

    wind = current.get(
        "wind_speed_10m", 0
    )

    gusts = current.get(
        "wind_gusts_10m", 0
    )

    visibility = current.get(
        "visibility", 0
    )


    score = 0

    factors = []


    # -----------------------------
    # SNOWFALL
    # -----------------------------

    if snowfall >= 10:

        score += 30

        factors.append({
            "factor": "Snowfall",
            "level": "HIGH",
            "reason": "Recent snowfall signal is elevated."
        })

    elif snowfall >= 3:

        score += 15

        factors.append({
            "factor": "Snowfall",
            "level": "MODERATE",
            "reason": "Moderate snowfall signal detected."
        })

    else:

        score += 3

        factors.append({
            "factor": "Snowfall",
            "level": "LOW",
            "reason": "Low current snowfall signal."
        })


    # -----------------------------
    # WIND
    # -----------------------------

    if wind >= 60 or gusts >= 80:

        score += 30

        factors.append({
            "factor": "Wind",
            "level": "HIGH",
            "reason": "Strong wind or gust signal detected."
        })

    elif wind >= 35 or gusts >= 50:

        score += 18

        factors.append({
            "factor": "Wind",
            "level": "MODERATE",
            "reason": "Moderate wind loading conditions."
        })

    else:

        score += 5

        factors.append({
            "factor": "Wind",
            "level": "LOW",
            "reason": "Lower wind signal detected."
        })


    # -----------------------------
    # TEMPERATURE
    # -----------------------------

    if temperature > 2:

        score += 20

        factors.append({
            "factor": "Temperature",
            "level": "WARM",
            "reason": "Temperature is relatively warm."
        })

    elif temperature > -5:

        score += 10

        factors.append({
            "factor": "Temperature",
            "level": "MODERATE",
            "reason": "Temperature is in an intermediate range."
        })

    else:

        score += 5

        factors.append({
            "factor": "Temperature",
            "level": "COLD",
            "reason": "Temperature is relatively cold."
        })


    # -----------------------------
    # VISIBILITY
    # -----------------------------

    if 0 < visibility < 2000:

        score += 15

        factors.append({
            "factor": "Visibility",
            "level": "LOW",
            "reason": "Visibility is reduced."
        })

    else:

        score += 3

        factors.append({
            "factor": "Visibility",
            "level": "GOOD",
            "reason": "No major visibility reduction detected."
        })


    score = min(score, 100)


    if score >= 70:

        category = "ELEVATED"

    elif score >= 40:

        category = "MODERATE"

    else:

        category = "LOW SIGNAL"


    return {

        "score": score,

        "category": category,

        "factors": factors,

        "model": "8W-RULES-V1",

        "experimental": True

    }