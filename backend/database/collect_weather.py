import asyncio
from datetime import datetime

from database.connection import SessionLocal
from database.models import Mountain, WeatherObservation
from services.weather import get_weather


async def collect_weather():

    db = SessionLocal()

    try:

        mountains = db.query(Mountain).all()

        print("\n8W WEATHER COLLECTION")
        print(f"Mountains found: {len(mountains)}")
        print("-" * 50)

        successful = 0
        failed = 0

        for mountain in mountains:

            print(f"Fetching {mountain.name}...")

            try:

                weather = await get_weather(
                    mountain.latitude,
                    mountain.longitude
                )

                current = weather.get("current", {})

                observation_time = current.get("time")

                observation = WeatherObservation(

                    mountain_id=mountain.id,

                    timestamp=(
                        datetime.fromisoformat(observation_time)
                        if observation_time
                        else datetime.utcnow()
                    ),

                    temperature=current.get(
                        "temperature_2m"
                    ),

                    snowfall=current.get(
                        "snowfall"
                    ),

                    snow_depth=current.get(
                        "snow_depth"
                    ),

                    wind_speed=current.get(
                        "wind_speed_10m"
                    ),

                    wind_gust=current.get(
                        "wind_gusts_10m"
                    ),

                    wind_direction=current.get(
                        "wind_direction_10m"
                    ),

                    visibility=current.get(
                        "visibility"
                    ),

                    precipitation=current.get(
                        "precipitation"
                    )
                )

                db.add(observation)
                db.commit()

                successful += 1

                print(
                    f"  ✓ Saved observation #{observation.id}"
                )

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"  ✗ Failed for {mountain.name} "
                    f"(ID {mountain.id}): {repr(error)}"
                )

        print("-" * 50)

        print(
            f"Completed: {successful} successful, "
            f"{failed} failed"
        )

    finally:

        db.close()


if __name__ == "__main__":

    asyncio.run(
        collect_weather()
    )