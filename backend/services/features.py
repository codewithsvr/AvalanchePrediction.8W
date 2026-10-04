from datetime import datetime, timedelta

from database.connection import SessionLocal
from database.models import Mountain, WeatherObservation


def get_features(mountain_id: int):

    db = SessionLocal()

    try:

        now = datetime.utcnow()

        # -----------------------------------------
        # Get recent observations
        # -----------------------------------------

        observations = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.mountain_id == mountain_id
            )
            .order_by(
                WeatherObservation.timestamp.desc()
            )
            .limit(100)
            .all()
        )

        if not observations:
            return None

        current = observations[0]

        # -----------------------------------------
        # Helper: find observation nearest to target
        # -----------------------------------------

        def nearest_observation(
            hours_ago,
            tolerance_hours
        ):

            target = now - timedelta(
                hours=hours_ago
            )

            candidates = []

            for obs in observations:

                difference_hours = abs(
                    (
                        obs.timestamp - target
                    ).total_seconds()
                ) / 3600

                if difference_hours <= tolerance_hours:

                    candidates.append(
                        (
                            difference_hours,
                            obs
                        )
                    )

            if not candidates:
                return None

            candidates.sort(
                key=lambda item: item[0]
            )

            return candidates[0][1]

        # -----------------------------------------
        # Historical observations
        # -----------------------------------------

        obs_6h = nearest_observation(
            6,
            2
        )

        obs_24h = nearest_observation(
            24,
            3
        )

        obs_72h = nearest_observation(
            72,
            6
        )

        # -----------------------------------------
        # Temperature change
        # -----------------------------------------

        temperature_change_6h = None

        if (
            obs_6h
            and current.temperature is not None
            and obs_6h.temperature is not None
        ):

            temperature_change_6h = (
                current.temperature
                - obs_6h.temperature
            )

        temperature_change_24h = None

        if (
            obs_24h
            and current.temperature is not None
            and obs_24h.temperature is not None
        ):

            temperature_change_24h = (
                current.temperature
                - obs_24h.temperature
            )

        # -----------------------------------------
        # Wind change
        # -----------------------------------------

        wind_change_6h = None

        if (
            obs_6h
            and current.wind_speed is not None
            and obs_6h.wind_speed is not None
        ):

            wind_change_6h = (
                current.wind_speed
                - obs_6h.wind_speed
            )

        # -----------------------------------------
        # Snowfall accumulation
        #
        # Multiple observations can exist within
        # the same hour.
        #
        # Keep only the latest observation from
        # each hour to avoid double-counting.
        # -----------------------------------------

        hourly_snowfall = {}

        for obs in observations:

            if obs.snowfall is None:
                continue

            age_hours = (
                now - obs.timestamp
            ).total_seconds() / 3600

            if age_hours < 0:
                continue

            if age_hours <= 72:

                hour_key = obs.timestamp.replace(
                    minute=0,
                    second=0,
                    microsecond=0
                )

                if (
                    hour_key not in hourly_snowfall
                    or obs.timestamp
                    > hourly_snowfall[hour_key]["timestamp"]
                ):

                    hourly_snowfall[hour_key] = {
                        "timestamp": obs.timestamp,
                        "snowfall": obs.snowfall
                    }

        # -----------------------------------------
        # Calculate 24h snowfall
        # -----------------------------------------

        snowfall_24h = 0.0

        cutoff_24h = now - timedelta(
            hours=24
        )

        for data in hourly_snowfall.values():

            if data["timestamp"] >= cutoff_24h:

                snowfall_24h += data["snowfall"]

        # -----------------------------------------
        # Calculate 72h snowfall
        # -----------------------------------------

        snowfall_72h = 0.0

        cutoff_72h = now - timedelta(
            hours=72
        )

        for data in hourly_snowfall.values():

            if data["timestamp"] >= cutoff_72h:

                snowfall_72h += data["snowfall"]

        # -----------------------------------------
        # Maximum wind gust in 24h
        # -----------------------------------------

        max_gust_24h = None

        gusts = []

        cutoff_24h = now - timedelta(
            hours=24
        )

        for obs in observations:

            if obs.timestamp < cutoff_24h:
                continue

            if obs.wind_gust is not None:

                gusts.append(
                    obs.wind_gust
                )

        if gusts:

            max_gust_24h = max(gusts)

        # -----------------------------------------
        # Visibility change
        # -----------------------------------------

        visibility_change_6h = None

        if (
            obs_6h
            and current.visibility is not None
            and obs_6h.visibility is not None
        ):

            visibility_change_6h = (
                current.visibility
                - obs_6h.visibility
            )

        # -----------------------------------------
        # Return features
        # -----------------------------------------

        return {

            "mountain_id": mountain_id,

            "current": {

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

                "visibility":
                    current.visibility
            },

            "features": {

                "temperature_change_6h":
                    temperature_change_6h,

                "temperature_change_24h":
                    temperature_change_24h,

                "wind_change_6h":
                    wind_change_6h,

                "snowfall_24h":
                    snowfall_24h,

                "snowfall_72h":
                    snowfall_72h,

                "max_gust_24h":
                    max_gust_24h,

                "visibility_change_6h":
                    visibility_change_6h
            },

            "observations_available":
                len(observations)
        }

    finally:

        db.close()