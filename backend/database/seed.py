from database.connection import SessionLocal
from database.models import Mountain
from data.peaks import PEAKS


def seed_mountains():

    db = SessionLocal()

    try:

        existing_count = db.query(Mountain).count()

        if existing_count > 0:

            print(
                f"Database already contains "
                f"{existing_count} mountains."
            )

            return


        for index, peak in enumerate(PEAKS, start=1):

            mountain = Mountain(

                id=index,

                name=peak["name"],

                elevation=peak["elevation"],

                range=peak["range"],

                region=peak["region"],

                country=peak["country"],

                latitude=peak["lat"],

                longitude=peak["lon"],

                route=peak["route"]

            )

            db.add(mountain)


        db.commit()

        print(
            f"Successfully inserted "
            f"{len(PEAKS)} mountains."
        )


    except Exception as error:

        db.rollback()

        print(
            "Database seeding failed:"
        )

        print(error)


    finally:

        db.close()


if __name__ == "__main__":

    seed_mountains()