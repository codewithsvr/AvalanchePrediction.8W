import asyncio
import httpx


async def get_weather(
    latitude: float,
    longitude: float
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "snowfall",
            "snow_depth",
            "visibility",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m"
        ]),

<<<<<<< HEAD
=======

>>>>>>> e756ead (Fix live weather API)
        "timezone": "UTC"
    }


    # Try up to 3 times
    for attempt in range(1, 4):

        try:

            async with httpx.AsyncClient(timeout=30) as client:

                response = await client.get(
                    url,
                    params=params
                )

                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as error:

            status = error.response.status_code

            if status in (502, 503, 504):

                print(
                    f"    Weather server returned "
                    f"{status} "
                    f"(attempt {attempt}/3)"
                )

                if attempt < 3:

                    wait_time = attempt * 3

                    print(
                        f"    Retrying in "
                        f"{wait_time} seconds..."
                    )

                    await asyncio.sleep(wait_time)

                else:

                    raise

            else:

                raise

        except (
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ConnectError,
            httpx.ReadError
        ) as error:

            print(
                f"    Weather request failed "
                f"(attempt {attempt}/3): {error}"
            )

            if attempt < 3:

                wait_time = attempt * 2

                print(
                    f"    Retrying in "
                    f"{wait_time} seconds..."
                )

                await asyncio.sleep(wait_time)

            else:

                raise
